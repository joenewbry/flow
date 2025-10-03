# 🎙️ Audio Recorder & Transcriber

A Python script that records system audio and transcribes it to text in real-time. Perfect for capturing Zoom calls, meetings, and other audio sessions for your personal history.

## ✨ Features

- **Real-time transcription** using OpenAI's Whisper model
- **Session management** with organized file structure
- **Multiple output formats** (audio files, text transcripts, JSON metadata)
- **Configurable chunk processing** for efficient transcription
- **Cross-platform support** (macOS, Linux, Windows)
- **Graceful shutdown** with Ctrl+C
- **Detailed session summaries**

## 🚀 Quick Start

### 1. Setup (One-time)

```bash
# Run the setup script
./setup_audio_recorder.sh

# Or manually:
source audio_env/bin/activate
pip install -r audio_requirements.txt
```

### 2. Start Recording

```bash
# Activate the environment
source audio_env/bin/activate

# Start recording with default settings
python audio_recorder.py

# Or with custom options
python audio_recorder.py --session-name "zoom-meeting-2024" --model small
```

### 3. Stop Recording

Press `Ctrl+C` to stop recording. The script will:
- Save the complete audio file
- Finalize the transcript
- Create a session summary
- Save all metadata to JSON

## 📁 Output Structure

Each session creates a folder with:

```
audio_sessions/
└── session_20241230_143022/
    ├── session_20241230_143022.wav          # Complete audio recording
    ├── session_20241230_143022_transcript.txt # Real-time transcript
    └── session_20241230_143022_session.json   # Session metadata
```

## ⚙️ Configuration Options

```bash
python audio_recorder.py --help
```

### Available Options:

- `--output-dir`: Directory for recordings (default: `audio_sessions`)
- `--model`: Whisper model size (`tiny`, `base`, `small`, `medium`, `large`)
- `--chunk-duration`: Seconds per transcription chunk (default: 30)
- `--session-name`: Custom session name (default: auto-generated)

### Model Comparison:

| Model  | Size | Speed | Accuracy | Best For |
|--------|------|-------|----------|----------|
| tiny   | 39MB | Fastest | Good | Quick testing |
| base   | 74MB | Fast | Better | General use |
| small  | 244MB | Medium | Good | Balanced |
| medium | 769MB | Slow | Very Good | High accuracy |
| large  | 1550MB | Slowest | Best | Maximum accuracy |

## 🎯 Use Cases

### Zoom Calls
```bash
python audio_recorder.py --session-name "team-standup-$(date +%Y%m%d)" --model base
```

### Long Meetings
```bash
python audio_recorder.py --model small --chunk-duration 60
```

### High-Quality Transcription
```bash
python audio_recorder.py --model large --chunk-duration 20
```

## 🔧 System Requirements

### macOS
```bash
brew install portaudio
```

### Ubuntu/Debian
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
```

### Windows
Usually works out of the box with `pip install pyaudio`

## 📝 Output Examples

### Transcript File
```
[14:30:22] Welcome everyone to today's team standup meeting.
[14:30:35] Let's start by going around and sharing what we worked on yesterday.
[14:31:02] I spent most of my time debugging the authentication issue we discussed.
[14:31:15] The problem was in the token validation logic.

--- Session Summary ---
Session ID: team-standup-20241230
Start Time: 2024-12-30 14:30:15
End Time: 2024-12-30 15:15:42
Duration: 0:45:27
Total Transcript Entries: 127
```

### JSON Metadata
```json
{
  "session_id": "team-standup-20241230",
  "start_time": "2024-12-30T14:30:15.123456",
  "end_time": "2024-12-30T15:15:42.789012",
  "duration": "0:45:27.665556",
  "transcript": [
    {
      "timestamp": "2024-12-30T14:30:22.456789",
      "text": "Welcome everyone to today's team standup meeting.",
      "confidence": 0.95
    }
  ],
  "audio_file": "team-standup-20241230.wav"
}
```

## 🛠️ Troubleshooting

### No Audio Device Found
- Check system audio settings
- Ensure microphone permissions are granted
- Try running with different input devices

### Poor Transcription Quality
- Use a larger Whisper model (`--model large`)
- Reduce chunk duration (`--chunk-duration 15`)
- Ensure good audio quality (close to microphone)

### High CPU Usage
- Use a smaller model (`--model tiny` or `--model base`)
- Increase chunk duration (`--chunk-duration 60`)

### Permission Errors
- On macOS: Grant microphone access in System Preferences
- On Linux: Check audio group membership (`sudo usermod -a -G audio $USER`)

## 🔒 Privacy & Legal Notes

- **Personal Use Only**: This tool is designed for recording your own audio sessions
- **Legal Compliance**: Ensure you have permission to record all participants
- **Data Security**: All recordings are stored locally on your machine
- **Zoom Compliance**: Check your organization's policies before recording meetings

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📄 License

This project is for personal use. Please respect privacy laws and obtain consent before recording others.

