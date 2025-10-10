#!/bin/bash

# Background Audio Recording Service Startup Script
# This script starts the background audio recording service

echo "🎙️  Starting Background Audio Recording Service..."

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

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
    echo "   To start ChromaDB, run: cd refinery && python -m chromadb.cli.cli run --host localhost --port 8000"
fi

# Check for ffmpeg (required for system audio capture on macOS)
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

# Start the background audio recorder
echo "🚀 Starting background audio recorder..."
echo "   - Model: base (good balance of speed/accuracy)"
echo "   - Chunk duration: 30 seconds"
echo "   - Minimum recording: 10 seconds"
echo "   - Output: audio_sessions/"
echo ""
echo "📝 Logs will be written to: audio_background.log"
echo "🛑 To stop: Press Ctrl+C or kill the process"
echo ""

# Run the background recorder
python audio_background_recorder.py \
    --model base \
    --chunk-duration 30 \
    --min-duration 10 \
    --output-dir audio_sessions

echo "✅ Background audio recorder stopped."
