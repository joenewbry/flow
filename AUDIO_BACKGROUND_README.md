# 🎙️ Background Audio Recording System

An intelligent background service that automatically captures **ALL audio** on your computer - both microphone (what you say) and system audio (YouTube, Zoom, music, etc.) - transcribes it using OpenAI Whisper API, and stores it in ChromaDB alongside your screen OCR data.

## ✨ Features

- **🔄 Automatic Detection**: Monitors audio and starts recording when activity is detected
- **🎤 Dual Capture**: Records BOTH microphone (your voice) AND system audio
- **🔊 Complete Coverage**: Captures YouTube, Zoom calls, music, all computer sounds
- **🤖 Real-time Transcription**: Uses OpenAI Whisper API for accurate speech-to-text
- **📝 Markdown Storage**: Saves transcripts as readable `.md` files in `refinery/data/audio/`
- **🔍 ChromaDB Integration**: Stores transcripts in `screen_ocr_history` collection with `data_type: "audio"` tag
- **🔗 Unified Search**: Search audio and OCR data together or filter by type
- **⚡ Background Service**: Runs continuously in the background like your other Flow services
- **🧠 Smart Filtering**: Only keeps recordings longer than 10 seconds, discards silence
- **📊 Structured Data**: Saves audio files, markdown transcripts, and metadata

**What Gets Recorded:**
- 🎤 Your microphone (what you say)
- 🔊 System audio (YouTube, Zoom, music, notifications)
- 💬 Both sides of video calls
- 🎵 Any audio playing on your computer

## 🚀 Quick Start

### 1. **Install BlackHole** (for system audio capture)
```bash
# Install BlackHole virtual audio device
brew install blackhole-2ch

# Configure Audio MIDI Setup (see AUDIO_SETUP_GUIDE.md for details)
# - Create Multi-Output Device with your speakers + BlackHole
# - Set system output to this Multi-Output device
```

### 2. **Set up your environment**
```bash
# Run setup script
./setup_audio_recorder.sh

# Add your OpenAI API key to .env file
echo "OPENAI_API_KEY=sk-your-key-here" >> .env
```

### 3. **Start the Background Service**
```bash
./start_audio_background.sh
```

### 4. **What You'll See**
```
🎙️  Starting Background Audio Recording Service...
🐍 Activating audio environment...
🔍 Checking ChromaDB connection...
🚀 Starting background audio recorder...
   - Using OpenAI Whisper API for transcription
   - Chunk duration: 30 seconds
   - Minimum recording: 10 seconds
   - Output: refinery/data/audio/ (.md and .json files)
   - ChromaDB: screen_ocr_history collection (tagged as 'audio')
ChromaDB connected to localhost:8000
Using screen_ocr_history collection in ChromaDB
✅ Background audio monitoring started!
🔍 Listening for audio activity...
```

### 5. **Test It Out**
The service will automatically capture:
- 🎤 **Your voice** when you speak into the microphone
- 🔊 **YouTube videos** playing in your browser
- 💬 **Zoom calls** (both you and other participants)
- 🎵 **Music** playing on your computer
- 🔔 **Any system sounds** or notifications

All audio is:
- Recorded in 30-second chunks
- Transcribed in real-time using OpenAI Whisper API
- Saved as markdown files in `refinery/data/audio/`
- Stored in ChromaDB with `data_type: "audio"` tag
- Searchable alongside your screen OCR data

### 6. **Stop the Service**
Press `Ctrl+C` or kill the process

## 📁 Output Structure

Each detected audio session creates files in `refinery/data/audio/`:

```
refinery/data/audio/
├── auto_20241015_143022.wav          # Audio recording (backup)
├── auto_20241015_143022.md           # Markdown transcript with timestamps
└── auto_20241015_143022.json         # Session metadata

Example markdown content:
# Audio Transcript: auto_20241015_143022

**Session Start:** 2024-10-15T14:30:22

---

## [14:30:25]

Welcome everyone to today's standup meeting...

## [14:31:02]

Let me share what I worked on yesterday...
```

## 🔧 Configuration Options

```bash
python audio_background_recorder.py --help
```

### Key Options:
- `--output-dir`: Directory to save recordings (default: `refinery/data/audio`)
- `--chunk-duration`: Transcription chunk size (default: 30s)
- `--min-duration`: Minimum recording length to keep (default: 10s)
- `--silence-threshold`: Audio level for silence detection (default: 0.01)

### About OpenAI Whisper API

The system uses **OpenAI's Whisper API** (`whisper-1` model) for transcription:
- **High Accuracy**: State-of-the-art transcription quality
- **Cloud-based**: No local model loading or GPU required
- **Fast Processing**: Real-time transcription of 30-second chunks
- **Cost**: ~$0.006 per minute of audio (very affordable)
- **Languages**: Supports 50+ languages automatically detected

## 🔍 ChromaDB Integration

Audio transcripts are automatically stored in the **same ChromaDB collection** as your screen OCR data (`screen_ocr_history`) but with a different tag:

### Metadata Structure:
```json
{
  "timestamp": "2024-10-15T14:30:22.456789",
  "session_id": "auto_20241015_143022",
  "source": "background_audio_recording",
  "data_type": "audio",              // Tag to differentiate from OCR
  "task_category": "audio_transcript",
  "text_length": 45,
  "word_count": 8,
  "extracted_text": "Welcome everyone to today's standup..."
}
```

### Unified Search:

You can search audio and OCR data together:
```python
# Search everything (audio + OCR)
results = collection.query(
    query_texts=["project deadline"],
    n_results=10
)

# Search only audio
results = collection.query(
    query_texts=["meeting discussion"],
    where={"data_type": "audio"},
    n_results=10
)

# Search only OCR (screenshots)
results = collection.query(
    query_texts=["github repository"],
    where={"data_type": "ocr"},
    n_results=10
)
```

Access your data using:
- **Dashboard**: Web interface at http://localhost:8081
- **MCP Server**: API access for Claude/other tools
- **Direct ChromaDB**: Query the `screen_ocr_history` collection

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
# Required: ffmpeg for audio capture
brew install ffmpeg

# Required for system audio: BlackHole virtual audio device
brew install blackhole-2ch

# Then configure Audio MIDI Setup (see AUDIO_SETUP_GUIDE.md)
```

### Audio Permissions
- Grant microphone access when prompted
- Configure Multi-Output Device for system audio (required)
- See `AUDIO_SETUP_GUIDE.md` for complete setup instructions

### What You Get:
- **With BlackHole configured**: Microphone + System Audio (everything)
- **Without BlackHole**: Microphone only (still useful but limited)

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
- OpenAI Whisper API is generally very accurate
- Ensure good audio quality from your system
- Check that ffmpeg is capturing audio correctly

### ChromaDB Connection Issues
- Ensure ChromaDB is running: `curl http://localhost:8000/api/v1/heartbeat`
- Start ChromaDB: `cd refinery && python -m chromadb.cli.cli run --host localhost --port 8000`

### OpenAI API Errors
- Verify your `OPENAI_API_KEY` is correct in `.env` file
- Check your OpenAI account has credits
- Audio files must be under 25MB for the API

## 📈 Next Steps

1. **Test with a Zoom call** to verify system audio capture
2. **Search transcripts** in the Dashboard
3. **Integrate with your workflow** using the MCP server
4. **Fine-tune settings** based on your usage patterns

The background audio recorder is now part of your Flow system - it will quietly capture and transcribe audio while you work, making everything searchable later!
