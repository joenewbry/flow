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

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found!"
    echo "   Please install Python 3 first."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "audio_env" ]; then
    echo "🐍 Creating virtual environment..."
    python3 -m venv audio_env
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment!"
        echo "   Try running: python3 -m venv audio_env"
        exit 1
    fi
else
    echo "✓ Virtual environment already exists"
fi

# Activate the audio environment
echo "🐍 Activating audio_env..."
source audio_env/bin/activate

# Check if pip is available
if ! command -v pip &> /dev/null; then
    echo "❌ pip not found!"
    echo ""
    echo "📋 To install pip, try one of these options:"
    echo ""
    echo "   Option 1 - Using ensurepip (recommended):"
    echo "     python3 -m ensurepip --upgrade"
    echo ""
    echo "   Option 2 - Using get-pip.py:"
    echo "     curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py"
    echo "     python3 get-pip.py"
    echo ""
    echo "   Option 3 - On macOS with Homebrew:"
    echo "     brew install python3"
    echo ""
    echo "   Option 4 - On Ubuntu/Debian:"
    echo "     sudo apt-get update"
    echo "     sudo apt-get install python3-pip"
    echo ""
    echo "After installing pip, run this setup script again."
    exit 1
fi

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

