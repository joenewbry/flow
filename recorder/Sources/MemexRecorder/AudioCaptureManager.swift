import Foundation

/// Orchestrates system audio + microphone capture with timed file rotation.
final class AudioCaptureManager {
    let systemWriter: AudioFileWriter
    let micWriter: AudioFileWriter
    let systemCapture: SystemAudioCapture
    let micCapture: MicrophoneCapture
    let rotationInterval: TimeInterval

    private var rotationTimer: DispatchSourceTimer?

    init(outputDir: URL, format: String, rotationInterval: TimeInterval) {
        // Create separate subdirs for system and mic audio
        let systemDir = outputDir.appendingPathComponent("system")
        let micDir = outputDir.appendingPathComponent("mic")

        try? FileManager.default.createDirectory(at: systemDir, withIntermediateDirectories: true)
        try? FileManager.default.createDirectory(at: micDir, withIntermediateDirectories: true)

        self.systemWriter = AudioFileWriter(outputDir: systemDir, format: format)
        self.micWriter = AudioFileWriter(outputDir: micDir, format: format)
        self.systemCapture = SystemAudioCapture(writer: systemWriter)
        self.micCapture = MicrophoneCapture(writer: micWriter)
        self.rotationInterval = rotationInterval
    }

    func start() async {
        // Start system audio
        do {
            try await systemCapture.start()
        } catch {
            log("System audio failed: \(error)")
            log("  (This requires Screen Recording permission)")
        }

        // Start microphone
        do {
            try micCapture.start()
        } catch {
            log("Microphone failed: \(error)")
            log("  (This requires Microphone permission)")
        }

        // Schedule file rotation
        startRotationTimer()

        log("Audio capture manager running (rotation every \(Int(rotationInterval))s)")
    }

    func stop() async {
        stopRotationTimer()
        await systemCapture.stop()
        micCapture.stop()
        systemWriter.finalize()
        micWriter.finalize()
        log("Audio capture manager stopped")
    }

    // MARK: - File rotation

    private func startRotationTimer() {
        let timer = DispatchSource.makeTimerSource(queue: .global(qos: .utility))
        timer.schedule(
            deadline: .now() + rotationInterval,
            repeating: rotationInterval
        )
        timer.setEventHandler { [weak self] in
            self?.rotateFiles()
        }
        timer.resume()
        self.rotationTimer = timer
    }

    private func stopRotationTimer() {
        rotationTimer?.cancel()
        rotationTimer = nil
    }

    private func rotateFiles() {
        log("Rotating audio files...")
        systemWriter.rotate()
        micWriter.rotate()
    }
}
