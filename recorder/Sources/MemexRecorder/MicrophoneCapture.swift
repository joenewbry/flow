import AVFoundation

/// Captures microphone audio using AVAudioEngine.
final class MicrophoneCapture {
    private let engine = AVAudioEngine()
    private let writer: AudioFileWriter
    private(set) var isRunning = false

    init(writer: AudioFileWriter) {
        self.writer = writer
    }

    func start() throws {
        let inputNode = engine.inputNode
        let inputFormat = inputNode.outputFormat(forBus: 0)

        guard inputFormat.sampleRate > 0 && inputFormat.channelCount > 0 else {
            throw RecorderError.noMicrophone
        }

        inputNode.installTap(onBus: 0, bufferSize: 4096, format: inputFormat) { [weak self] buffer, _ in
            self?.writer.write(pcmBuffer: buffer)
        }

        engine.prepare()
        try engine.start()
        isRunning = true
        log("Microphone capture started (\(inputFormat.sampleRate)Hz, \(inputFormat.channelCount)ch)")
    }

    func stop() {
        engine.inputNode.removeTap(onBus: 0)
        engine.stop()
        isRunning = false
        log("Microphone capture stopped")
    }
}
