# Screen Tracker Desktop App Demo

## 🎯 Quick Start Guide

### Prerequisites
1. Node.js 18+ installed
2. Anthropic API key
3. Optional: ChromaDB server running

### Installation Steps

1. **Install dependencies**:
```bash
npm install
```

2. **Create environment file**:
```bash
# Create .env file with your API key
echo "ANTHROPIC_API_KEY=your_api_key_here" > .env
```

3. **Launch the desktop app**:
```bash
# Option 1: Using npm
npm start

# Option 2: Using the launch script
./start-app.sh

# Option 3: Using the Node launcher
node launch.js
```

## 🖥️ Desktop App Features

### Dashboard Overview
The app provides a comprehensive dashboard with these key sections:

#### 📊 Statistics Card
- **Screenshots**: Total count of captured screenshots
- **Analysis Files**: Number of processed analysis files
- **Total Words**: Cumulative word count from OCR/analysis
- **Total Characters**: Total character count extracted
- **Total Size**: Disk space usage

#### ⚙️ System Status Card
- **Screen Tracking**: Real-time tracking status (Active/Inactive)
- **ChromaDB Server**: Database connectivity status
- **Control buttons**: Start/Stop tracking functionality

#### 📸 Recent Screenshots
- Interactive list of your latest screenshots
- Click any screenshot to open it in your default image viewer
- Shows file size and creation info

#### 🔍 Recent Analysis
- List of recent AI analysis results
- Word and character counts for each analysis
- Click to view detailed analysis in text editor

#### 🔗 MCP Integration
- **Vector Store**: ChromaDB connectivity status
- **Claude Desktop**: Configuration management
- Quick links to configuration files

#### 💾 Storage Management
- Breakdown of storage usage
- Quick access to screenshots and analysis folders
- Storage analytics and trends

### 🎮 Interactive Controls

#### Start/Stop Tracking
- **Start Tracking**: Begins screenshot capture and analysis
- **Stop Tracking**: Safely stops the tracking process
- Real-time process monitoring with live logs

#### File Management
- **Open Screenshots**: Direct access to screenshots folder
- **Open Analysis**: Access to analysis results folder
- **Open Config**: Quick access to Claude Desktop configuration

#### System Monitoring
- **Refresh Status**: Updates all system status indicators
- **Live Logs**: Real-time output from tracking processes
- **Error Handling**: User-friendly error messages and recovery

## 🔧 Technical Features

### Process Management
- **Subprocess Control**: Runs tracking in background process
- **Error Recovery**: Automatic restart on failures
- **Resource Monitoring**: Memory and CPU usage tracking

### Real-time Updates
- **Auto-refresh**: Statistics update every 30 seconds
- **Live Status**: Tracking status updates every 5 seconds
- **Dynamic UI**: Responsive interface with real-time feedback

### File System Integration
- **Native File Access**: Direct OS file system integration
- **Cross-platform**: Works on Windows, macOS, and Linux
- **Permissions**: Handles file permissions gracefully

## 🚀 Usage Scenarios

### Daily Workflow Tracking
1. Launch the desktop app
2. Click "Start Tracking"
3. Continue with your regular computer usage
4. Monitor statistics in real-time
5. Stop tracking when done

### Analysis Review
1. View recent screenshots and analysis
2. Click on files to open them
3. Review extracted text and AI insights
4. Export data for further analysis

### System Maintenance
1. Monitor storage usage
2. Check ChromaDB connectivity
3. Review system logs for issues
4. Manage configuration files

## 📱 User Interface

### Modern Design
- **Glass morphism**: Translucent cards with blur effects
- **Gradient backgrounds**: Beautiful color transitions
- **Smooth animations**: Hover effects and transitions
- **Responsive layout**: Adapts to different screen sizes

### Status Indicators
- **Green pulse**: Active/healthy status
- **Red solid**: Inactive/error status
- **Loading spinners**: Operations in progress
- **Real-time updates**: Live data refresh

### Interactive Elements
- **Hover effects**: Visual feedback on interactive elements
- **Click actions**: Direct file opening and navigation
- **Keyboard shortcuts**: Quick actions via keyboard
- **Context menus**: Right-click options (via app menu)

## 🔍 Troubleshooting

### Common Issues

**App won't start**:
- Check Node.js installation
- Verify all dependencies installed
- Check for port conflicts

**No statistics showing**:
- Ensure screenshot directories exist
- Check file permissions
- Verify tracking has run previously

**ChromaDB connection failed**:
- Start ChromaDB server: `chroma run --host localhost --port 8000`
- Check firewall settings
- Verify network connectivity

**Tracking won't start**:
- Check screen capture permissions
- Verify API key configuration
- Review system logs for errors

### Debug Mode
Run with development tools:
```bash
npm run dev
```

This opens DevTools for debugging and inspecting the app.

## 🔄 Integration with Existing System

The desktop app seamlessly integrates with your existing screen tracking setup:

- **Same data**: Uses the same screenshots and analysis files
- **Compatible**: Works with existing ChromaDB collections
- **Non-intrusive**: Doesn't modify your existing workflow
- **Additive**: Provides additional monitoring and control capabilities

## 🎯 Benefits

### Improved User Experience
- **Visual monitoring**: See your tracking system status at a glance
- **Easy control**: Start/stop tracking with one click
- **Quick access**: Open files and folders instantly
- **Real-time feedback**: Live updates on system performance

### Better System Management
- **Resource monitoring**: Track storage usage and growth
- **Health checks**: Monitor all system components
- **Error visibility**: Clear error messages and logs
- **Configuration management**: Easy access to settings

### Enhanced Productivity
- **Streamlined workflow**: All controls in one place
- **Time savings**: Quick access to data and files
- **Better insights**: Real-time statistics and trends
- **Reduced friction**: Eliminate command-line operations

This desktop app transforms your screen tracking system from a command-line tool into a modern, user-friendly application that's easy to monitor and control.