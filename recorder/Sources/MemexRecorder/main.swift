import Foundation

// MARK: - Logging

func log(_ message: String) {
    let formatter = DateFormatter()
    formatter.dateFormat = "HH:mm:ss"
    let timestamp = formatter.string(from: Date())
    FileHandle.standardError.write(Data("[\(timestamp)] \(message)\n".utf8))
}

// MARK: - Argument parsing

func parseArgs() -> (outputDir: String, format: String, rotationInterval: Int) {
    let args = CommandLine.arguments
    var outputDir = "."
    var format = "m4a"
    var rotationInterval = 300

    var i = 1
    while i < args.count {
        switch args[i] {
        case "--output-dir":
            if i + 1 < args.count { outputDir = args[i + 1]; i += 1 }
        case "--format":
            if i + 1 < args.count { format = args[i + 1]; i += 1 }
        case "--rotation-interval":
            if i + 1 < args.count { rotationInterval = Int(args[i + 1]) ?? 300; i += 1 }
        case "--help", "-h":
            print("memex-recorder - Audio capture for Memex")
            print()
            print("Usage: memex-recorder [options]")
            print()
            print("Options:")
            print("  --output-dir <path>         Output directory (default: current dir)")
            print("  --format <m4a|wav>          Audio format (default: m4a)")
            print("  --rotation-interval <secs>  File rotation interval (default: 300)")
            print("  --help, -h                  Show this help")
            exit(0)
        default:
            break
        }
        i += 1
    }

    return (outputDir, format, rotationInterval)
}

// MARK: - Main

let config = parseArgs()
let outputURL = URL(fileURLWithPath: config.outputDir, isDirectory: true)

// Ensure output directory exists
try FileManager.default.createDirectory(at: outputURL, withIntermediateDirectories: true)

log("memex-recorder starting")
log("  Output: \(outputURL.path)")
log("  Format: \(config.format)")
log("  Rotation: every \(config.rotationInterval)s")

let manager = AudioCaptureManager(
    outputDir: outputURL,
    format: config.format,
    rotationInterval: TimeInterval(config.rotationInterval)
)

// Handle SIGTERM/SIGINT for graceful shutdown
let shutdownSource = DispatchSource.makeSignalSource(signal: SIGTERM, queue: .main)
signal(SIGTERM, SIG_IGN)
shutdownSource.setEventHandler {
    log("Received SIGTERM, shutting down...")
    Task {
        await manager.stop()
        log("Shutdown complete")
        exit(0)
    }
}
shutdownSource.resume()

let interruptSource = DispatchSource.makeSignalSource(signal: SIGINT, queue: .main)
signal(SIGINT, SIG_IGN)
interruptSource.setEventHandler {
    log("Received SIGINT, shutting down...")
    Task {
        await manager.stop()
        log("Shutdown complete")
        exit(0)
    }
}
interruptSource.resume()

// Start capture
Task {
    await manager.start()
}

// Run the main run loop (keeps process alive)
RunLoop.main.run()
