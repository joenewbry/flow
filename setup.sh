#!/bin/bash

# Flow Setup Script
# Comprehensive setup for the Flow screen history and search system

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Detect operating system
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

# Install system dependencies
install_system_deps() {
    local os=$(detect_os)
    
    log_info "Installing system dependencies for $os..."
    
    case $os in
        "macos")
            if ! command_exists brew; then
                log_error "Homebrew not found. Please install Homebrew first:"
                log_info "Run: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
                exit 1
            fi
            
            log_info "Installing Tesseract OCR..."
            brew install tesseract
            
            log_info "Installing PortAudio (for audio features)..."
            brew install portaudio
            ;;
            
        "linux")
            if command_exists apt-get; then
                log_info "Installing dependencies via apt..."
                sudo apt-get update
                sudo apt-get install -y tesseract-ocr tesseract-ocr-eng python3-dev python3-venv portaudio19-dev
            elif command_exists yum; then
                log_info "Installing dependencies via yum..."
                sudo yum install -y tesseract python3-devel python3-venv portaudio-devel
            elif command_exists pacman; then
                log_info "Installing dependencies via pacman..."
                sudo pacman -S tesseract python python-virtualenv portaudio
            else
                log_error "Unsupported Linux distribution. Please install tesseract and python3-venv manually."
                exit 1
            fi
            ;;
            
        "windows")
            log_warning "Windows detected. Please ensure you have:"
            log_info "1. Python 3.10+ installed from python.org"
            log_info "2. Tesseract OCR installed from GitHub releases"
            log_info "3. Git installed from git-scm.com"
            read -p "Press Enter to continue once dependencies are installed..."
            ;;
            
        *)
            log_error "Unsupported operating system: $OSTYPE"
            exit 1
            ;;
    esac
}

# Check Python version
check_python() {
    log_info "Checking Python version..."
    
    if command_exists python3; then
        local version=$(python3 --version 2>&1 | cut -d' ' -f2)
        local major=$(echo $version | cut -d'.' -f1)
        local minor=$(echo $version | cut -d'.' -f2)
        
        if [[ $major -eq 3 ]] && [[ $minor -ge 10 ]]; then
            log_success "Python $version found"
            return 0
        else
            log_error "Python 3.10+ required, found $version"
            return 1
        fi
    else
        log_error "Python 3 not found"
        return 1
    fi
}

# Setup virtual environment for a component
setup_venv() {
    local component=$1
    local requirements_file=$2
    
    log_info "Setting up virtual environment for $component..."
    
    cd "$component"
    
    # Remove existing venv if it exists
    if [[ -d ".venv" ]]; then
        log_warning "Removing existing virtual environment..."
        rm -rf .venv
    fi
    
    # Create new virtual environment
    python3 -m venv .venv
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    if [[ -f "$requirements_file" ]]; then
        log_info "Installing $component dependencies..."
        pip install -r "$requirements_file"
    else
        log_warning "No requirements file found for $component"
    fi
    
    # Deactivate virtual environment
    deactivate
    
    cd ..
    
    log_success "$component virtual environment setup complete"
}

# Create configuration files
create_config() {
    log_info "Creating configuration files..."
    
    # Create .env file
    if [[ ! -f ".env" ]]; then
        cat > .env << EOF
# ChromaDB Configuration
CHROMA_HOST=localhost
CHROMA_PORT=8000

# Dashboard Configuration
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=8080

# Screen Capture Configuration
CAPTURE_INTERVAL=60
MAX_CONCURRENT_OCR=4

# Logging Configuration
LOG_LEVEL=INFO

# Audio Configuration (optional)
AUDIO_ENABLED=false
AUDIO_DEVICE_INDEX=0
EOF
        log_success "Created .env configuration file"
    else
        log_info ".env file already exists, skipping..."
    fi
    
    # Create refinery config
    if [[ ! -f "refinery/config.json" ]]; then
        cat > refinery/config.json << EOF
{
  "capture_interval": 60,
  "max_concurrent_ocr": 4,
  "auto_start": false,
  "data_retention_days": 90,
  "compress_old_data": true,
  "screens": {
    "enabled": true,
    "naming_convention": "screen_{index}"
  },
  "ocr": {
    "language": "eng",
    "confidence_threshold": 30
  }
}
EOF
        log_success "Created refinery configuration file"
    else
        log_info "Refinery config already exists, skipping..."
    fi
}

# Create startup scripts
create_startup_scripts() {
    log_info "Creating startup scripts..."
    
    # Create start-all script
    cat > start-all.sh << 'EOF'
#!/bin/bash

# Flow System Startup Script
# Starts all Flow components in the correct order

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to start component in background
start_component() {
    local name=$1
    local command=$2
    local logfile=$3
    
    log_info "Starting $name..."
    nohup bash -c "$command" > "$logfile" 2>&1 &
    echo $! > "${name}.pid"
    sleep 2
    
    if kill -0 $(cat "${name}.pid") 2>/dev/null; then
        log_success "$name started successfully (PID: $(cat "${name}.pid"))"
    else
        echo "❌ Failed to start $name"
        return 1
    fi
}

log_info "Starting Flow System..."

# Check if ChromaDB port is available
if check_port 8000; then
    log_info "Port 8000 is already in use (ChromaDB may already be running)"
else
    # Start ChromaDB
    start_component "chromadb" \
        "cd refinery && source .venv/bin/activate && chroma run --host localhost --port 8000" \
        "logs/chromadb.log"
fi

# Wait for ChromaDB to be ready
log_info "Waiting for ChromaDB to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/api/v1/heartbeat >/dev/null 2>&1; then
        log_success "ChromaDB is ready"
        break
    fi
    sleep 1
    if [[ $i -eq 30 ]]; then
        echo "❌ ChromaDB failed to start within 30 seconds"
        exit 1
    fi
done

# Start Screen Capture
start_component "screen-capture" \
    "cd refinery && source .venv/bin/activate && python run.py" \
    "logs/screen-capture.log"

# Start Dashboard
start_component "dashboard" \
    "cd dashboard && source .venv/bin/activate && python app.py" \
    "logs/dashboard.log"

# Start MCP Server
start_component "mcp-server" \
    "cd mcp-server && source .venv/bin/activate && python server.py" \
    "logs/mcp-server.log"

log_success "All Flow components started successfully!"
echo ""
echo "🌐 Dashboard: http://localhost:8080"
echo "🔍 ChromaDB: http://localhost:8000"
echo ""
echo "📋 To stop all components, run: ./stop-all.sh"
echo "📊 To view logs, check the logs/ directory"
EOF

    # Create stop-all script
    cat > stop-all.sh << 'EOF'
#!/bin/bash

# Flow System Shutdown Script
# Stops all Flow components gracefully

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to stop component
stop_component() {
    local name=$1
    local pidfile="${name}.pid"
    
    if [[ -f "$pidfile" ]]; then
        local pid=$(cat "$pidfile")
        if kill -0 "$pid" 2>/dev/null; then
            log_info "Stopping $name (PID: $pid)..."
            kill "$pid"
            
            # Wait for process to stop
            for i in {1..10}; do
                if ! kill -0 "$pid" 2>/dev/null; then
                    log_success "$name stopped"
                    rm "$pidfile"
                    return 0
                fi
                sleep 1
            done
            
            # Force kill if still running
            log_info "Force stopping $name..."
            kill -9 "$pid" 2>/dev/null || true
            rm "$pidfile"
            log_success "$name force stopped"
        else
            log_info "$name was not running"
            rm "$pidfile"
        fi
    else
        log_info "No PID file found for $name"
    fi
}

log_info "Stopping Flow System..."

# Stop components in reverse order
stop_component "mcp-server"
stop_component "dashboard"
stop_component "screen-capture"
stop_component "chromadb"

# Kill any remaining Flow processes
log_info "Cleaning up any remaining processes..."
pkill -f "python.*flow" 2>/dev/null || true
pkill -f "chroma run" 2>/dev/null || true

log_success "Flow system stopped"
EOF

    # Create logs directory
    mkdir -p logs
    
    # Make scripts executable
    chmod +x start-all.sh stop-all.sh
    
    log_success "Startup scripts created"
}

# Verify installation
verify_installation() {
    log_info "Verifying installation..."
    
    local errors=0
    
    # Check Python environments
    for component in refinery dashboard mcp-server; do
        if [[ -d "$component/.venv" ]]; then
            log_success "$component virtual environment exists"
        else
            log_error "$component virtual environment missing"
            ((errors++))
        fi
    done
    
    # Check Tesseract
    if command_exists tesseract; then
        local version=$(tesseract --version 2>&1 | head -1)
        log_success "Tesseract found: $version"
    else
        log_error "Tesseract not found"
        ((errors++))
    fi
    
    # Check configuration files
    if [[ -f ".env" ]]; then
        log_success "Configuration file (.env) exists"
    else
        log_error "Configuration file (.env) missing"
        ((errors++))
    fi
    
    if [[ $errors -eq 0 ]]; then
        log_success "Installation verification passed!"
        return 0
    else
        log_error "Installation verification failed with $errors errors"
        return 1
    fi
}

# Main setup function
main() {
    echo "🚀 Flow Setup Script"
    echo "===================="
    echo ""
    
    # Check if we're in the Flow directory
    if [[ ! -f "README.md" ]] || [[ ! -d "refinery" ]]; then
        log_error "Please run this script from the Flow project root directory"
        exit 1
    fi
    
    # Install system dependencies
    install_system_deps
    
    # Check Python
    if ! check_python; then
        log_error "Please install Python 3.10+ and try again"
        exit 1
    fi
    
    # Setup virtual environments
    setup_venv "refinery" "flow-requirements.txt"
    setup_venv "dashboard" "requirements.txt"
    setup_venv "mcp-server" "requirements.txt"
    
    # Create configuration files
    create_config
    
    # Create startup scripts
    create_startup_scripts
    
    # Verify installation
    if verify_installation; then
        echo ""
        log_success "Flow setup completed successfully! 🎉"
        echo ""
        echo "📋 Next steps:"
        echo "1. Start the system: ./start-all.sh"
        echo "2. Open dashboard: http://localhost:8080"
        echo "3. Configure Claude Desktop (see README.md)"
        echo ""
        echo "📖 For detailed instructions, see:"
        echo "   - INSTALLATION.md - Complete installation guide"
        echo "   - TROUBLESHOOTING.md - Common issues and solutions"
        echo "   - README.md - Project overview and usage"
    else
        log_error "Setup completed with errors. Please check the output above."
        exit 1
    fi
}

# Run main function
main "$@"
