// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "MemexRecorder",
    platforms: [.macOS(.v13)],
    targets: [
        .executableTarget(
            name: "memex-recorder",
            path: "Sources/MemexRecorder",
            linkerSettings: [
                .linkedFramework("ScreenCaptureKit"),
                .linkedFramework("AVFoundation"),
                .linkedFramework("CoreMedia"),
                .linkedFramework("CoreAudio"),
            ]
        ),
    ]
)
