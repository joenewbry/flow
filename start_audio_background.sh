#!/bin/bash

# Background Audio Recording Service Startup Script
# This script starts the background audio recording service

echo "🎙️  Starting Background Audio Recording Service..."

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if .env file exists with OPENAI_API_KEY
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please create one with your OPENAI_API_KEY."
    echo "   Example: echo 'OPENAI_API_KEY=your-key-here' > .env"
    exit 1
fi

# Check if OPENAI_API_KEY is set in .env
if ! grep -q "OPENAI_API_KEY" .env; then
    echo "❌ OPENAI_API_KEY not found in .env file."
    echo "   Add it to your .env file: OPENAI_API_KEY=your-key-here"
    exit 1
fi

# Check if audio environment exists
if [ ! -d "audio_env" ]; then
    echo "❌ Audio environment not found. Please run setup_audio_recorder.sh first."
    exit 1
fi

# Activate the audio environment
echo "🐍 Activating audio environment..."
source audio_env/bin/activate

# Check if ChromaDB is running
echo "🔍 Checking ChromaDB connection..."
if ! curl -s http://localhost:8000/api/v1/heartbeat > /dev/null 2>&1; then
    echo "⚠️  ChromaDB not running on localhost:8000"
    echo "   Audio will be saved locally but not stored in ChromaDB"
    echo "   To start ChromaDB, run: cd refinery && chroma run --host localhost --port 8000"
fi

# Check for ffmpeg (required for audio capture on macOS)
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  ffmpeg not found. Installing via Homebrew..."
    if command -v brew &> /dev/null; then
        brew install ffmpeg
    else
        echo "❌ Please install ffmpeg manually:"
        echo "   brew install ffmpeg"
        exit 1
    fi
fi

# Check for BlackHole (recommended for capturing system audio)
echo "🔍 Checking for BlackHole virtual audio device..."
if system_profiler SPAudioDataType 2>/dev/null | grep -q "BlackHole"; then
    echo "✅ BlackHole detected - will capture BOTH microphone AND system audio"
    echo "   (YouTube, Zoom, music, all computer sounds)"
else
    echo "⚠️  BlackHole not detected - will capture MICROPHONE ONLY"
    echo ""
    echo "   To capture ALL audio (microphone + system audio):"
    echo "   1. Install BlackHole: brew install blackhole-2ch"
    echo "   2. See AUDIO_SETUP_GUIDE.md for complete setup instructions"
    echo ""
    read -p "   Continue with microphone-only? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled. Install BlackHole and try again."
        exit 1
    fi
fi

# Create audio data directory if it doesn't exist
mkdir -p refinery/data/audio

# Start the background audio recorder
echo ""
echo "🚀 Starting background audio recorder..."
echo "   - Using OpenAI Whisper API for transcription"
echo "   - Capturing: Microphone + System Audio (if BlackHole is set up)"
echo "   - Chunk duration: 30 seconds"
echo "   - Minimum recording: 10 seconds"
echo "   - Output: refinery/data/audio/ (.md and .json files)"
echo "   - ChromaDB: screen_ocr_history collection (tagged as 'audio')"
echo ""
echo "📝 Logs will be written to: audio_background.log"
echo "🛑 To stop: Press Ctrl+C or kill the process"
echo ""
echo "🎤 AUDIO CAPTURE:"
echo "   ✅ Microphone (your voice)"
if system_profiler SPAudioDataType 2>/dev/null | grep -q "BlackHole"; then
    echo "   ✅ System Audio (YouTube, Zoom, music, all sounds)"
else
    echo "   ❌ System Audio (install BlackHole to enable)"
fi
echo ""

# Run the background recorder
python audio_background_recorder.py \
    --chunk-duration 30 \
    --min-duration 10 \
    --output-dir refinery/data/audio

echo "✅ Background audio recorder stopped."
