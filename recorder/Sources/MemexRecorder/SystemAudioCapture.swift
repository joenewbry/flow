import ScreenCaptureKit
import CoreMedia
import AVFoundation

/// Captures system audio (Zoom, Teams, browser, etc.) using ScreenCaptureKit.
final class SystemAudioCapture: NSObject, SCStreamOutput {
    private var stream: SCStream?
    private let writer: AudioFileWriter
    private(set) var isRunning = false

    init(writer: AudioFileWriter) {
        self.writer = writer
    }

    func start() async throws {
        // Get available content
        let content = try await SCShareableContent.excludingDesktopWindows(false, onScreenWindowsOnly: false)

        guard let display = content.displays.first else {
            throw RecorderError.noDisplay
        }

        // Filter: capture from display, exclude nothing
        let filter = SCContentFilter(display: display, excludingWindows: [])

        // Configure: audio only, minimize video overhead
        let config = SCStreamConfiguration()
        config.capturesAudio = true
        config.excludesCurrentProcessAudio = true
        config.channelCount = 2
        config.sampleRate = 48000

        // Minimize video (can't fully disable, so use tiny frame)
        config.width = 2
        config.height = 2
        config.minimumFrameInterval = CMTime(value: 1, timescale: 1)  // 1 FPS

        let stream = SCStream(filter: filter, configuration: config, delegate: nil)
        try stream.addStreamOutput(self, type: .audio, sampleHandlerQueue: .global(qos: .userInitiated))
        try await stream.startCapture()

        self.stream = stream
        self.isRunning = true
        log("System audio capture started")
    }

    func stop() async {
        guard let stream = stream else { return }
        do {
            try await stream.stopCapture()
        } catch {
            log("Error stopping system audio: \(error)")
        }
        self.stream = nil
        self.isRunning = false
        log("System audio capture stopped")
    }

    // MARK: - SCStreamOutput

    func stream(_ stream: SCStream, didOutputSampleBuffer sampleBuffer: CMSampleBuffer, of type: SCStreamOutputType) {
        guard type == .audio else { return }
        writer.write(sampleBuffer: sampleBuffer)
    }
}

enum RecorderError: Error, CustomStringConvertible {
    case noDisplay
    case noMicrophone

    var description: String {
        switch self {
        case .noDisplay: return "No display found for system audio capture"
        case .noMicrophone: return "No microphone input available"
        }
    }
}
