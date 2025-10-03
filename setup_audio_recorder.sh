#!/bin/bash

# Audio Recorder Setup Script
# This script sets up the audio recording environment

echo "🎙️  Setting up Audio Recorder..."

# Check if we're on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "📱 Detected macOS"
    
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo "❌ Homebrew not found. Please install Homebrew first:"
        echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
    
    # Install PortAudio (required for PyAudio)
    echo "🔧 Installing PortAudio..."
    brew install portaudio
    
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "🐧 Detected Linux"
    
    # Install PortAudio for Linux
    echo "🔧 Installing PortAudio..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y portaudio19-dev python3-pyaudio
    elif command -v yum &> /dev/null; then
        sudo yum install -y portaudio-devel
    else
        echo "❌ Unsupported Linux distribution. Please install portaudio manually."
        exit 1
    fi
fi

# Activate the audio environment
echo "🐍 Activating audio_env..."
source audio_env/bin/activate

# Install Python requirements
echo "📦 Installing Python requirements..."
pip install -r audio_requirements.txt

echo "✅ Setup complete!"
echo ""
echo "🚀 Usage:"
echo "   source audio_env/bin/activate"
echo "   python audio_recorder.py"
echo ""
echo "📖 For more options:"
echo "   python audio_recorder.py --help"

