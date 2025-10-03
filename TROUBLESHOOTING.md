# Flow Troubleshooting Guide

This guide covers common issues, error messages, and solutions for the Flow system. Use this guide to diagnose and resolve problems quickly.

## 🚨 Emergency Quick Fixes

### System Not Responding
```bash
# Stop all Flow processes
pkill -f "python.*flow"
pkill -f "chroma"

# Restart in order
cd refinery && source .venv/bin/activate && chroma run --host localhost --port 8000 &
cd refinery && source .venv/bin/activate && python run.py &
cd dashboard && source .venv/bin/activate && python app.py &
```

### Dashboard Won't Load
```bash
# Check if dashboard is running
curl http://localhost:8080/health

# If not responding, restart dashboard
cd dashboard && source .venv/bin/activate && python app.py
```

### Complete System Reset
```bash
# Stop all processes
pkill -f "python.*flow"
pkill -f "chroma"

# Clear temporary data (CAUTION: This removes captured data)
rm -rf refinery/chroma/*
rm -rf refinery/data/ocr/*

# Restart system
# Follow startup sequence in INSTALLATION.md
```

## 🔍 Diagnostic Tools

### System Health Check
```bash
# Check all required ports
lsof -i :8000  # ChromaDB
lsof -i :8080  # Dashboard

# Check Python environments
cd refinery && source .venv/bin/activate && python -c "import chromadb, pytesseract; print('Refinery OK')"
cd dashboard && source .venv/bin/activate && python -c "import fastapi, uvicorn; print('Dashboard OK')"
cd mcp-server && source .venv/bin/activate && python -c "import mcp; print('MCP OK')"

# Check Tesseract
tesseract --version

# Check disk space
df -h
```

### Log Analysis
```bash
# View recent dashboard logs (if running)
curl http://localhost:8080/api/logs

# Check system logs (macOS)
log show --predicate 'process CONTAINS "python"' --last 1h

# Check system logs (Linux)
journalctl -u flow* --since "1 hour ago"
```

## 🐛 Common Issues & Solutions

### Installation Issues

#### Python Version Conflicts
**Symptoms:**
- `python: command not found`
- Version conflicts between Python installations

**Solutions:**
```bash
# Check Python version
python3 --version

# Use specific Python version
python3.11 -m venv .venv

# On macOS with multiple Python versions
/usr/local/bin/python3.11 -m venv .venv

# Update PATH if needed
export PATH="/usr/local/bin:$PATH"
```

#### Virtual Environment Issues
**Symptoms:**
- `ModuleNotFoundError` despite installation
- Wrong Python interpreter being used

**Solutions:**
```bash
# Recreate virtual environment
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Verify correct environment
which python
which pip
```

#### Tesseract Installation Problems
**Symptoms:**
- `TesseractNotFoundError`
- OCR processing fails

**Solutions:**
```bash
# macOS - Reinstall Tesseract
brew uninstall tesseract
brew install tesseract

# Linux - Install with language packs
sudo apt remove tesseract-ocr
sudo apt install tesseract-ocr tesseract-ocr-eng

# Windows - Add to PATH
# Add Tesseract installation directory to system PATH
# Usually: C:\Program Files\Tesseract-OCR

# Test installation
tesseract --list-langs
```

### Runtime Issues

#### ChromaDB Connection Failed
**Symptoms:**
- `Connection refused` errors
- Dashboard shows ChromaDB as "Stopped"

**Solutions:**
```bash
# Check if ChromaDB is running
curl http://localhost:8000/api/v1/heartbeat

# If not running, start ChromaDB
cd refinery
source .venv/bin/activate
chroma run --host localhost --port 8000

# Check for port conflicts
lsof -i :8000
# If port is in use, kill the process or use different port
chroma run --host localhost --port 8001

# Update configuration for new port
# Edit .env file: CHROMA_PORT=8001
```

#### Screen Capture Permission Denied
**Symptoms:**
- Empty screenshots
- Permission errors in logs
- No OCR data generated

**Solutions:**

**macOS:**
```bash
# Grant screen recording permission
# System Preferences > Security & Privacy > Privacy > Screen Recording
# Add Terminal or your terminal app
# Restart terminal application

# Verify permission
screencapture -t png test.png
ls -la test.png
rm test.png
```

**Linux:**
```bash
# Check X11 access
echo $DISPLAY
xhost +local:

# For Wayland, ensure proper permissions
# May need to run with sudo or adjust user permissions
```

**Windows:**
```bash
# Usually no special permissions needed
# Check if antivirus is blocking screen capture
# Temporarily disable antivirus and test
```

#### High CPU/Memory Usage
**Symptoms:**
- System slowdown
- Fan noise
- High resource usage in Activity Monitor/Task Manager

**Solutions:**
```bash
# Reduce capture frequency
# Edit refinery/config.json
{
  "capture_interval": 120,  # Increase from 60 to 120 seconds
  "max_concurrent_ocr": 2   # Reduce from 4 to 2
}

# Monitor resource usage
top -p $(pgrep -f "python.*flow")

# Restart with lower settings
```

#### OCR Processing Slow/Failing
**Symptoms:**
- Long delays between captures
- OCR files not being created
- High CPU usage during OCR

**Solutions:**
```bash
# Check OCR queue
ls -la refinery/data/screenshots/
ls -la refinery/data/ocr/

# Reduce concurrent OCR processes
# Edit refinery/config.json
{
  "max_concurrent_ocr": 1
}

# Clear OCR backlog
rm refinery/data/screenshots/*.png

# Test Tesseract directly
tesseract test_image.png output -l eng
```

### Dashboard Issues

#### Dashboard Won't Start
**Symptoms:**
- `Address already in use` error
- Dashboard not accessible at localhost:8080

**Solutions:**
```bash
# Check what's using port 8080
lsof -i :8080

# Kill process using port
kill -9 $(lsof -t -i:8080)

# Or use different port
cd dashboard
source .venv/bin/activate
python app.py --port 8081

# Update bookmarks to use new port
```

#### Dashboard Loads But Shows Errors
**Symptoms:**
- Dashboard loads but components show errors
- API calls failing
- Empty data displays

**Solutions:**
```bash
# Check dashboard logs
curl http://localhost:8080/api/logs

# Verify API endpoints
curl http://localhost:8080/api/stats
curl http://localhost:8080/health

# Check ChromaDB connection from dashboard
curl http://localhost:8080/api/search?q=test

# Restart dashboard with debug logging
cd dashboard
source .venv/bin/activate
LOG_LEVEL=DEBUG python app.py
```

#### Real-time Updates Not Working
**Symptoms:**
- Dashboard doesn't update automatically
- Stale data displayed
- WebSocket connection issues

**Solutions:**
```bash
# Check WebSocket connection in browser
# Open browser dev tools > Network > WS tab
# Look for WebSocket connection errors

# Disable browser extensions that might block WebSockets
# Try in incognito/private mode

# Check firewall settings
# Ensure localhost connections are allowed

# Restart dashboard
cd dashboard && source .venv/bin/activate && python app.py
```

### MCP Server Issues

#### MCP Server Won't Start
**Symptoms:**
- Claude Desktop shows MCP connection errors
- MCP tools not available in Claude

**Solutions:**
```bash
# Test MCP server directly
cd mcp-server
source .venv/bin/activate
python server.py

# Check MCP dependencies
pip list | grep mcp

# Recreate MCP environment
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Make startup script executable
chmod +x start.sh
```

#### Claude Desktop Can't Connect to MCP
**Symptoms:**
- MCP server starts but Claude can't connect
- Tools not appearing in Claude Desktop

**Solutions:**
```bash
# Verify Claude Desktop config
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Check path in config matches actual path
ls -la /path/to/flow/mcp-server/start.sh

# Update config with absolute paths
{
  "mcpServers": {
    "flow": {
      "command": "/absolute/path/to/flow/mcp-server/start.sh"
    }
  }
}

# Restart Claude Desktop after config changes
```

#### MCP Tools Return Errors
**Symptoms:**
- Tools appear in Claude but return errors
- Search results empty or incorrect

**Solutions:**
```bash
# Test MCP tools individually
cd mcp-server
source .venv/bin/activate
python -c "
from tools.search import SearchTool
tool = SearchTool()
result = tool.search_screenshots('test', None, None, 10)
print(result)
"

# Check ChromaDB connection from MCP server
python -c "
import chromadb
client = chromadb.HttpClient(host='localhost', port=8000)
print(client.heartbeat())
"

# Verify OCR data exists
ls -la ../refinery/data/ocr/
```

### Search & Data Issues

#### Search Returns No Results
**Symptoms:**
- All searches return empty results
- Dashboard shows zero captures

**Solutions:**
```bash
# Check if OCR data exists
ls -la refinery/data/ocr/
wc -l refinery/data/ocr/*.json

# Verify ChromaDB has data
cd refinery
source .venv/bin/activate
python -c "
import chromadb
client = chromadb.HttpClient(host='localhost', port=8000)
collection = client.get_collection('screen_ocr_history')
print(f'Collection count: {collection.count()}')
"

# Reindex existing data
python -c "
from lib.chroma_client import ChromaClient
client = ChromaClient()
client.reindex_all_data()
"
```

#### Search Results Irrelevant
**Symptoms:**
- Search returns results but they're not relevant
- Vector search not working properly

**Solutions:**
```bash
# Check embedding model
cd refinery
source .venv/bin/activate
python -c "
import chromadb
client = chromadb.HttpClient(host='localhost', port=8000)
collection = client.get_collection('screen_ocr_history')
print(collection.metadata)
"

# Try more specific search terms
# Use natural language instead of keywords
# Include context in search queries

# Rebuild embeddings if needed
python -c "
from lib.chroma_client import ChromaClient
client = ChromaClient()
client.rebuild_collection()
"
```

#### Data Corruption
**Symptoms:**
- ChromaDB errors
- Corrupted JSON files
- Inconsistent data

**Solutions:**
```bash
# Backup current data
cp -r refinery/data/ backup/data-$(date +%Y%m%d)/
cp -r refinery/chroma/ backup/chroma-$(date +%Y%m%d)/

# Validate JSON files
cd refinery/data/ocr/
for file in *.json; do
  python -m json.tool "$file" > /dev/null || echo "Corrupted: $file"
done

# Remove corrupted files
# (Manual step - review each corrupted file)

# Rebuild ChromaDB collection
cd refinery
source .venv/bin/activate
python -c "
from lib.chroma_client import ChromaClient
client = ChromaClient()
client.rebuild_collection()
"
```

## 🔧 Performance Optimization

### Reduce Resource Usage
```bash
# Optimize capture settings
# Edit refinery/config.json
{
  "capture_interval": 120,        # Longer intervals
  "max_concurrent_ocr": 2,        # Fewer parallel processes
  "compress_old_data": true,      # Enable compression
  "data_retention_days": 30       # Shorter retention
}

# Clean up old data
find refinery/data/ocr/ -name "*.json" -mtime +30 -delete
find refinery/data/screenshots/ -name "*.png" -mtime +1 -delete
```

### Improve Search Performance
```bash
# Optimize ChromaDB
cd refinery
source .venv/bin/activate
python -c "
import chromadb
client = chromadb.HttpClient(host='localhost', port=8000)
# Consider adjusting collection settings for better performance
"

# Use more specific search queries
# Include date ranges in searches
# Limit search result counts
```

### Monitor System Health
```bash
# Check disk usage
du -sh refinery/data/
du -sh refinery/chroma/

# Monitor memory usage
ps aux | grep python | grep flow

# Check network connections
netstat -an | grep :8000
netstat -an | grep :8080
```

## 📊 Debugging Tools

### Enable Debug Logging
```bash
# Set debug logging in .env
echo "LOG_LEVEL=DEBUG" >> .env

# Restart components to pick up new log level
```

### Capture Debug Information
```bash
# Create debug report
cat > debug_report.txt << EOF
=== Flow Debug Report ===
Date: $(date)
OS: $(uname -a)
Python: $(python3 --version)

=== Port Status ===
$(lsof -i :8000 :8080)

=== Process Status ===
$(ps aux | grep -E "(python|chroma)" | grep -v grep)

=== Disk Usage ===
$(du -sh refinery/data/ refinery/chroma/ 2>/dev/null)

=== Recent Errors ===
$(tail -50 dashboard/logs/error.log 2>/dev/null || echo "No error log found")

=== Configuration ===
$(cat .env 2>/dev/null || echo "No .env file found")
EOF

echo "Debug report saved to debug_report.txt"
```

### Test Individual Components
```bash
# Test ChromaDB
curl -s http://localhost:8000/api/v1/heartbeat && echo "ChromaDB: OK" || echo "ChromaDB: FAILED"

# Test Dashboard
curl -s http://localhost:8080/health && echo "Dashboard: OK" || echo "Dashboard: FAILED"

# Test Tesseract
tesseract --version && echo "Tesseract: OK" || echo "Tesseract: FAILED"

# Test Screen Capture
cd refinery && source .venv/bin/activate && python -c "
from lib.screen_detection import capture_screens
screens = capture_screens()
print(f'Screen capture: {len(screens)} screens detected')
"
```

## 🆘 Getting Help

### Before Reporting Issues
1. **Check this troubleshooting guide** for your specific issue
2. **Run the debug tools** above to gather information
3. **Try the emergency quick fixes** to see if they resolve the issue
4. **Check recent changes** - did you update anything recently?

### Information to Include in Bug Reports
- Operating system and version
- Python version
- Error messages (full stack traces)
- Debug report output
- Steps to reproduce the issue
- Expected vs actual behavior

### Where to Get Help
1. **GitHub Issues**: [Create a new issue](https://github.com/yourusername/flow/issues)
2. **Email Support**: joenewbry+flow@gmail.com
3. **Community Discussions**: [GitHub Discussions](https://github.com/yourusername/flow/discussions)

### Emergency Contact
For critical issues affecting data integrity or security:
**Email**: joenewbry+flow+urgent@gmail.com

## 📚 Additional Resources

- [INSTALLATION.md](INSTALLATION.md) - Complete installation guide
- [README.md](README.md) - Project overview and basic usage
- [API.md](API.md) - API documentation for developers
- [CONTRIBUTING.md](CONTRIBUTING.md) - How to contribute to Flow

---

**Remember**: Most issues can be resolved by restarting components in the correct order. When in doubt, stop all processes and follow the startup sequence in the installation guide.
