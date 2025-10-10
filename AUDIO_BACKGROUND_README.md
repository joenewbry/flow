# 🎙️ Background Audio Recording System

An intelligent background service that automatically detects and records system audio (like Zoom calls), transcribes it to text, and stores it in ChromaDB for searchability.

## ✨ Features

- **🔄 Automatic Detection**: Monitors system audio and starts recording when activity is detected
- **🎯 System Audio Capture**: Records actual system audio (Zoom calls, meetings, etc.) not microphone
- **🤖 Real-time Transcription**: Uses OpenAI Whisper for accurate speech-to-text
- **🔍 ChromaDB Integration**: Stores transcripts in ChromaDB alongside your screen OCR data
- **⚡ Background Service**: Runs continuously in the background like your other Flow services
- **🧠 Smart Filtering**: Only keeps recordings longer than 10 seconds, discards silence
- **📊 Structured Data**: Saves audio files, transcripts, and metadata

## 🚀 Quick Start

### 1. **Start the Background Service**
```bash
./start_audio_background.sh
```

### 2. **What You'll See**
```
🎙️  Starting Background Audio Recording Service...
🐍 Activating audio environment...
🔍 Checking ChromaDB connection...
🚀 Starting background audio recorder...
🎙️  Starting background audio monitoring...
ChromaDB connected to localhost:8000
Audio collection initialized in ChromaDB
✅ Background audio monitoring started!
🔍 Listening for audio activity...
```

### 3. **During a Zoom Call**
The service will automatically:
- Detect audio activity
- Start recording
- Transcribe speech in real-time
- Store in ChromaDB for searching
- Save local files for backup

### 4. **Stop the Service**
Press `Ctrl+C` or kill the process

## 📁 Output Structure

Each detected audio session creates:

```
audio_sessions/
└── auto_20241003_143022/
    ├── auto_20241003_143022.wav          # Audio recording
    ├── auto_20241003_143022_transcript.txt # Transcript with timestamps
    └── auto_20241003_143022_session.json   # Session metadata
```

## 🔧 Configuration Options

```bash
python audio_background_recorder.py --help
```

### Key Options:
- `--model`: Whisper model (`tiny`, `base`, `small`, `medium`, `large`)
- `--chunk-duration`: Transcription chunk size (default: 30s)
- `--min-duration`: Minimum recording length to keep (default: 10s)
- `--silence-threshold`: Audio level for silence detection (default: 0.01)

### Performance Tuning:

| Model  | Speed | Accuracy | CPU Usage | Best For |
|--------|-------|----------|-----------|----------|
| tiny   | Fastest | Good | Low | Quick testing |
| base   | Fast | Better | Medium | **Recommended default** |
| small  | Medium | Good | Medium | High accuracy needs |
| medium | Slow | Very Good | High | Maximum accuracy |
| large  | Slowest | Best | Very High | Offline processing |

## 🔍 ChromaDB Integration

Audio transcripts are automatically stored in ChromaDB with metadata:

```json
{
  "timestamp": "2024-10-03T14:30:22.456789",
  "session_id": "auto_20241003_143022",
  "confidence": 0.95,
  "source": "background_audio_recording",
  "task_category": "audio_transcript",
  "text_length": 45,
  "word_count": 8
}
```

You can search audio transcripts alongside your screen OCR data using:
- **Dashboard**: Web interface at http://localhost:5000
- **MCP Server**: API access for Claude/other tools
- **Direct ChromaDB**: Query the `audio_transcripts` collection

## 🎯 Use Cases

### Automatic Meeting Recording
- Starts recording when Zoom/Teams/etc. begins
- Transcribes all speech automatically
- Searchable meeting history

### Background Documentation
- Captures important conversations
- Creates searchable knowledge base
- No manual intervention required

### Integration with Flow System
- Audio transcripts appear in search results
- Combined with screen OCR for complete context
- Part of your personal knowledge system

## 🛠️ System Requirements

### macOS Setup
```bash
# Required: ffmpeg for system audio capture
brew install ffmpeg

# Optional: BlackHole for better audio routing
# Download from: https://github.com/ExistentialAudio/BlackHole
```

### Audio Permissions
- Grant microphone access when prompted
- For system audio: May need to configure audio routing

## 🔒 Privacy & Legal

- **Local Processing**: All transcription happens on your machine
- **Personal Use**: Designed for your own audio sessions
- **Legal Compliance**: Ensure you have permission to record
- **Data Security**: Files stored locally, ChromaDB runs locally

## 🚦 Service Management

### Start with System
Add to your startup scripts or use a process manager like `pm2`:

```bash
# Using pm2 (install with: npm install -g pm2)
pm2 start start_audio_background.sh --name "audio-recorder"
pm2 save
pm2 startup
```

### Monitor Status
```bash
# Check if running
ps aux | grep audio_background_recorder

# View logs
tail -f audio_background.log
```

### Integration with Other Services
The audio recorder works alongside:
- **Refinery**: Screen capture and OCR
- **Dashboard**: Web interface for all data
- **MCP Server**: API access for tools

## 🔧 Troubleshooting

### No Audio Detected
- Check system audio settings
- Verify ffmpeg can access audio: `ffmpeg -f avfoundation -list_devices true -i ""`
- Consider installing BlackHole for better audio routing

### Poor Transcription Quality
- Use a larger model (`--model large`)
- Reduce chunk duration (`--chunk-duration 15`)
- Ensure good audio quality

### ChromaDB Connection Issues
- Ensure ChromaDB is running: `curl http://localhost:8000/api/v1/heartbeat`
- Start ChromaDB: `cd refinery && python -m chromadb.cli.cli run --host localhost --port 8000`

### High CPU Usage
- Use smaller model (`--model tiny`)
- Increase chunk duration (`--chunk-duration 60`)

## 📈 Next Steps

1. **Test with a Zoom call** to verify system audio capture
2. **Search transcripts** in the Dashboard
3. **Integrate with your workflow** using the MCP server
4. **Fine-tune settings** based on your usage patterns

The background audio recorder is now part of your Flow system - it will quietly capture and transcribe audio while you work, making everything searchable later!
