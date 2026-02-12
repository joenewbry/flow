import AVFoundation
import CoreMedia

/// Thread-safe audio file writer that handles CMSampleBuffer → PCM conversion and file rotation.
final class AudioFileWriter {
    private let outputDir: URL
    private let format: AVFileType
    private let fileExtension: String

    private var currentFile: AVAudioFile?
    private var currentFilePath: URL?
    private let outputFormat: AVAudioFormat
    private let lock = NSLock()

    init(outputDir: URL, format: String = "m4a") {
        self.outputDir = outputDir
        if format == "wav" {
            self.format = .wav
            self.fileExtension = "wav"
        } else {
            self.format = .m4a
            self.fileExtension = "m4a"
        }

        // Standard output format: 48kHz stereo float32
        self.outputFormat = AVAudioFormat(
            commonFormat: .pcmFormatFloat32,
            sampleRate: 48000,
            channels: 2,
            interleaved: false
        )!
    }

    /// Write a CMSampleBuffer (from ScreenCaptureKit or mic) to the current file.
    func write(sampleBuffer: CMSampleBuffer) {
        lock.lock()
        defer { lock.unlock() }

        guard let pcmBuffer = convertToPCMBuffer(sampleBuffer: sampleBuffer) else { return }
        ensureFileOpen()
        guard let file = currentFile else { return }

        do {
            try file.write(from: pcmBuffer)
        } catch {
            log("Failed to write audio: \(error)")
        }
    }

    /// Write a PCM buffer directly (from AVAudioEngine mic tap).
    func write(pcmBuffer: AVAudioPCMBuffer) {
        lock.lock()
        defer { lock.unlock() }

        // Convert to our output format if needed
        let buffer: AVAudioPCMBuffer
        if pcmBuffer.format == outputFormat {
            buffer = pcmBuffer
        } else if let converted = convertBuffer(pcmBuffer, to: outputFormat) {
            buffer = converted
        } else {
            return
        }

        ensureFileOpen()
        guard let file = currentFile else { return }

        do {
            try file.write(from: buffer)
        } catch {
            log("Failed to write mic audio: \(error)")
        }
    }

    /// Rotate to a new file. Closes current file and returns its path.
    @discardableResult
    func rotate() -> URL? {
        lock.lock()
        defer { lock.unlock() }
        return closeCurrentFile()
    }

    /// Finalize and close the current file.
    func finalize() {
        lock.lock()
        defer { lock.unlock() }
        _ = closeCurrentFile()
    }

    // MARK: - Private

    private func ensureFileOpen() {
        if currentFile != nil { return }

        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd'T'HH-mm-ss"
        let timestamp = formatter.string(from: Date())
        let filename = "audio_\(timestamp).\(fileExtension)"
        let filePath = outputDir.appendingPathComponent(filename)

        do {
            if fileExtension == "wav" {
                currentFile = try AVAudioFile(
                    forWriting: filePath,
                    settings: outputFormat.settings,
                    commonFormat: .pcmFormatFloat32,
                    interleaved: false
                )
            } else {
                // M4A with AAC encoding
                let settings: [String: Any] = [
                    AVFormatIDKey: kAudioFormatMPEG4AAC,
                    AVSampleRateKey: 48000,
                    AVNumberOfChannelsKey: 2,
                    AVEncoderBitRateKey: 128000,
                ]
                currentFile = try AVAudioFile(
                    forWriting: filePath,
                    settings: settings,
                    commonFormat: .pcmFormatFloat32,
                    interleaved: false
                )
            }
            currentFilePath = filePath
            log("Recording to: \(filePath.lastPathComponent)")
        } catch {
            log("Failed to create audio file: \(error)")
        }
    }

    private func closeCurrentFile() -> URL? {
        let path = currentFilePath
        currentFile = nil
        currentFilePath = nil
        if let path = path {
            log("Closed file: \(path.lastPathComponent)")
        }
        return path
    }

    private func convertToPCMBuffer(sampleBuffer: CMSampleBuffer) -> AVAudioPCMBuffer? {
        guard let formatDesc = CMSampleBufferGetFormatDescription(sampleBuffer),
              let asbd = CMAudioFormatDescriptionGetStreamBasicDescription(formatDesc)
        else { return nil }

        guard let sourceFormat = AVAudioFormat(streamDescription: asbd) else { return nil }

        let frameCount = CMSampleBufferGetNumSamples(sampleBuffer)
        guard frameCount > 0 else { return nil }

        guard let sourceBuffer = AVAudioPCMBuffer(
            pcmFormat: sourceFormat,
            frameCapacity: AVAudioFrameCount(frameCount)
        ) else { return nil }

        sourceBuffer.frameLength = AVAudioFrameCount(frameCount)

        // Copy sample data into the PCM buffer
        guard let blockBuffer = CMSampleBufferGetDataBuffer(sampleBuffer) else { return nil }

        var lengthAtOffset: Int = 0
        var totalLength: Int = 0
        var dataPointer: UnsafeMutablePointer<Int8>?

        let status = CMBlockBufferGetDataPointer(
            blockBuffer, atOffset: 0, lengthAtOffsetOut: &lengthAtOffset,
            totalLengthOut: &totalLength, dataPointerOut: &dataPointer
        )

        guard status == kCMBlockBufferNoErr, let data = dataPointer else { return nil }

        // ScreenCaptureKit delivers float32 non-interleaved audio.
        // Copy raw bytes into the source buffer's channel data.
        let bytesToCopy = min(totalLength, Int(frameCount) * Int(sourceFormat.streamDescription.pointee.mBytesPerFrame))

        if sourceFormat.isInterleaved {
            // Interleaved: single contiguous buffer
            if let dest = sourceBuffer.floatChannelData?[0] {
                memcpy(dest, data, bytesToCopy)
            }
        } else {
            // Non-interleaved: split across channel pointers
            if let dest = sourceBuffer.floatChannelData {
                let channelCount = Int(sourceFormat.channelCount)
                let bytesPerChannel = bytesToCopy / max(channelCount, 1)
                for ch in 0..<channelCount {
                    memcpy(dest[ch], data.advanced(by: ch * bytesPerChannel), bytesPerChannel)
                }
            }
        }

        // Convert to output format if needed
        if sourceFormat == outputFormat {
            return sourceBuffer
        }
        return convertBuffer(sourceBuffer, to: outputFormat)
    }

    private func convertBuffer(_ source: AVAudioPCMBuffer, to format: AVAudioFormat) -> AVAudioPCMBuffer? {
        guard let converter = AVAudioConverter(from: source.format, to: format) else { return nil }

        let ratio = format.sampleRate / source.format.sampleRate
        let outputFrameCount = AVAudioFrameCount(Double(source.frameLength) * ratio)
        guard let outputBuffer = AVAudioPCMBuffer(pcmFormat: format, frameCapacity: outputFrameCount) else { return nil }

        var error: NSError?
        var consumed = false
        converter.convert(to: outputBuffer, error: &error) { _, outStatus in
            if consumed {
                outStatus.pointee = .noDataNow
                return nil
            }
            consumed = true
            outStatus.pointee = .haveData
            return source
        }

        if let error = error {
            log("Audio conversion error: \(error)")
            return nil
        }

        return outputBuffer
    }
}
