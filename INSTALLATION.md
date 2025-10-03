# Flow Installation Guide

This comprehensive guide will walk you through setting up Flow on your system, from initial installation to running your first searches.

## 📋 Prerequisites

### System Requirements
- **Operating System**: macOS 10.15+, Windows 10+, or Linux (Ubuntu 18.04+)
- **Python**: Version 3.10 or higher
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 10GB free space (more for extended screen history)
- **Network**: Internet connection for initial setup

### Required Software

#### 1. Python 3.10+
**macOS (using Homebrew):**
```bash
brew install python@3.11
```

**Windows:**
Download from [python.org](https://www.python.org/downloads/) and install.

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-pip
```

#### 2. Tesseract OCR
**macOS:**
```bash
brew install tesseract
```

**Windows:**
Download from [GitHub releases](https://github.com/UB-Mannheim/tesseract/wiki) and install.

**Linux:**
```bash
sudo apt install tesseract-ocr
```

#### 3. Git
**macOS:**
```bash
brew install git
```

**Windows:**
Download from [git-scm.com](https://git-scm.com/download/win)

**Linux:**
```bash
sudo apt install git
```

### System Permissions

#### macOS Screen Recording Permission
1. Open **System Preferences** > **Security & Privacy** > **Privacy**
2. Select **Screen Recording** from the left sidebar
3. Click the lock icon and enter your password
4. Add Terminal (or your terminal app) to the list
5. Restart your terminal application

#### Windows Display Capture
No special permissions required for Windows.

#### Linux X11/Wayland
Ensure your user has access to the display server (usually automatic).

## 🚀 Installation Steps

### Step 1: Clone the Repository

```bash
# Clone Flow repository
git clone https://github.com/yourusername/flow.git
cd flow

# Verify the directory structure
ls -la
```

You should see directories: `dashboard/`, `mcp-server/`, `refinery/`, etc.

### Step 2: Set Up Screen Capture System

```bash
# Navigate to refinery directory
cd refinery

# Create Python virtual environment
python3 -m venv .venv

# Activate virtual environment
# macOS/Linux:
source .venv/bin/activate
# Windows:
# .venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r flow-requirements.txt

# Verify installation
python -c "import pytesseract; print('Tesseract OK')"
python -c "import chromadb; print('ChromaDB OK')"

# Return to project root
cd ..
```

### Step 3: Set Up Flow Dashboard

```bash
# Navigate to dashboard directory
cd dashboard

# Create Python virtual environment
python3 -m venv .venv

# Activate virtual environment
# macOS/Linux:
source .venv/bin/activate
# Windows:
# .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import fastapi; print('FastAPI OK')"
python -c "import uvicorn; print('Uvicorn OK')"

# Return to project root
cd ..
```

### Step 4: Set Up MCP Server

```bash
# Navigate to mcp-server directory
cd mcp-server

# Create Python virtual environment
python3 -m venv .venv

# Activate virtual environment
# macOS/Linux:
source .venv/bin/activate
# Windows:
# .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Make startup script executable (macOS/Linux only)
chmod +x start.sh

# Verify installation
python -c "import mcp; print('MCP OK')"

# Return to project root
cd ..
```

### Step 5: Create Configuration Files

#### Create Environment File
```bash
# Create .env file in project root
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
EOF
```

#### Create Refinery Configuration
```bash
# Create config file for screen capture
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
```

## 🏃‍♂️ First Run

### Step 1: Start ChromaDB Server

Open a new terminal window and run:

```bash
cd /path/to/flow/refinery
source .venv/bin/activate
chroma run --host localhost --port 8000
```

**Expected output:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://localhost:8000
```

### Step 2: Start Screen Capture

Open another terminal window and run:

```bash
cd /path/to/flow/refinery
source .venv/bin/activate
python run.py
```

**Expected output:**
```
2024-01-01 12:00:00 - INFO - Flow screen capture starting...
2024-01-01 12:00:00 - INFO - Detected 2 screens
2024-01-01 12:00:00 - INFO - ChromaDB connection established
2024-01-01 12:00:00 - INFO - Starting capture loop...
```

### Step 3: Start Flow Dashboard

Open another terminal window and run:

```bash
cd /path/to/flow/dashboard
source .venv/bin/activate
python app.py
```

**Expected output:**
```
INFO:     Started server process [67890]
INFO:     Waiting for application startup.
2024-01-01 12:00:00 - app - INFO - Starting Flow Dashboard...
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080
```

### Step 4: Access Dashboard

Open your web browser and navigate to:
**http://localhost:8080**

You should see the Flow Dashboard with:
- System status indicators
- Empty activity graph (will populate as data is captured)
- Search interface
- Configuration panels

### Step 5: Start MCP Server (Optional)

If you plan to use Claude Desktop integration:

```bash
cd /path/to/flow/mcp-server
./start.sh
```

**Expected output:**
```
Flow MCP Server starting...
MCP server running on stdio
```

## 🔧 Configuration

### Dashboard Configuration

1. Open the Flow Dashboard: http://localhost:8080
2. Navigate to the **System Configuration** section
3. Adjust settings as needed:
   - **Capture Interval**: How often to take screenshots (default: 60 seconds)
   - **Theme**: Choose light, dark, or auto theme
   - **Data Retention**: How long to keep OCR data (default: 90 days)

### Claude Desktop Integration

1. **Locate Claude Desktop Config File:**
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

2. **Add Flow MCP Server:**
   ```json
   {
     "mcpServers": {
       "flow": {
         "command": "/path/to/flow/mcp-server/start.sh"
       }
     }
   }
   ```

3. **Update the path** with your actual Flow installation directory

4. **Restart Claude Desktop**

## ✅ Verification

### Test Screen Capture
1. Wait 1-2 minutes after starting the capture system
2. Check the dashboard for activity in the graph
3. Verify OCR data files in `refinery/data/ocr/`

### Test Dashboard
1. Navigate to http://localhost:8080
2. Verify all sections load properly
3. Check system status shows "Running" for components
4. Test the search interface (may be empty initially)

### Test MCP Integration
1. Open Claude Desktop
2. Start a new conversation
3. Ask: "What can Flow do?"
4. Verify Flow tools are available and responding

## 🐛 Troubleshooting

### Common Issues

#### "Permission denied" on macOS
**Problem**: Screen recording permission not granted
**Solution**: 
1. Go to System Preferences > Security & Privacy > Privacy > Screen Recording
2. Add your terminal application
3. Restart terminal and try again

#### "Port already in use"
**Problem**: Another service is using port 8000 or 8080
**Solution**:
```bash
# Check what's using the port
lsof -i :8080

# Kill the process or use different port
cd dashboard && python app.py --port 8081
```

#### "Module not found" errors
**Problem**: Dependencies not installed correctly
**Solution**:
```bash
# Reactivate virtual environment and reinstall
cd dashboard  # or refinery, or mcp-server
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### ChromaDB connection failed
**Problem**: ChromaDB server not running or wrong port
**Solution**:
```bash
# Verify ChromaDB is running
curl http://localhost:8000/api/v1/heartbeat

# If not running, start it:
cd refinery && source .venv/bin/activate && chroma run --host localhost --port 8000
```

#### No OCR data captured
**Problem**: Tesseract not installed or configured properly
**Solution**:
```bash
# Test Tesseract installation
tesseract --version

# If not found, reinstall:
# macOS: brew install tesseract
# Ubuntu: sudo apt install tesseract-ocr
# Windows: Download from GitHub releases
```

### Performance Issues

#### High CPU usage
- Reduce capture interval in configuration
- Decrease `max_concurrent_ocr` setting
- Close unnecessary applications

#### High memory usage
- Enable data compression in settings
- Reduce data retention period
- Restart components periodically

#### Slow search results
- Wait for initial indexing to complete
- Check ChromaDB server performance
- Consider upgrading hardware

## 📊 Monitoring

### Dashboard Monitoring
- Check system status indicators regularly
- Monitor activity graphs for capture consistency
- Review system logs for errors

### Log Files
- **Dashboard logs**: Available in dashboard UI
- **Screen capture logs**: Console output or log files
- **ChromaDB logs**: ChromaDB server console

### Health Checks
The dashboard includes automatic health monitoring:
- System component status
- Error detection and recovery
- Performance metrics

## 🔄 Updates

### Updating Flow
```bash
# Navigate to Flow directory
cd /path/to/flow

# Pull latest changes
git pull origin main

# Update each component
cd refinery && source .venv/bin/activate && pip install -r flow-requirements.txt
cd ../dashboard && source .venv/bin/activate && pip install -r requirements.txt
cd ../mcp-server && source .venv/bin/activate && pip install -r requirements.txt
```

### Backup Before Updates
```bash
# Backup configuration and data
cp -r refinery/data/ backup/data-$(date +%Y%m%d)/
cp -r refinery/chroma/ backup/chroma-$(date +%Y%m%d)/
cp .env backup/env-$(date +%Y%m%d)
```

## 🎯 Next Steps

After successful installation:

1. **Let it run**: Allow Flow to capture data for a few hours or days
2. **Test searches**: Try searching for content you know you've viewed
3. **Configure settings**: Adjust capture interval and retention policies
4. **Set up Claude**: Configure Claude Desktop integration for AI-powered search
5. **Monitor performance**: Use the dashboard to track system health

## 📞 Getting Help

If you encounter issues not covered in this guide:

1. **Check the dashboard logs** for error messages
2. **Review the troubleshooting section** above
3. **Search existing issues** on GitHub
4. **Create a new issue** with detailed error information
5. **Email support**: joenewbry+flow@gmail.com

## 📚 Additional Resources

- [README.md](README.md) - Project overview and features
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Detailed troubleshooting guide
- [API.md](API.md) - API documentation for developers
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contributing guidelines

---

**Congratulations!** You now have Flow installed and running. Start capturing your screen history and enjoy intelligent search capabilities!
