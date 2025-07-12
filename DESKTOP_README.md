# Screen Tracker Desktop App

A beautiful Electron-based desktop application that provides a comprehensive dashboard for managing your screen tracking and analysis system.

## Features

### 📊 Real-time Statistics
- **Screenshot Count**: Total number of screenshots captured
- **OCR Analysis**: Total words and characters extracted from screenshots
- **Storage Usage**: Monitor total disk space used by screenshots and analysis files
- **Recent Activity**: View your most recent screenshots and analysis files

### ⚙️ System Control
- **Start/Stop Tracking**: Control the screen capture process directly from the dashboard
- **System Status**: Monitor the health of screen tracking and ChromaDB services
- **Real-time Logs**: View live output from the tracking system

### 🔗 MCP Integration Dashboard
- **ChromaDB Status**: Monitor vector store connectivity
- **Configuration Management**: Quick access to Claude Desktop configuration
- **Service Health**: Check the status of all system components

### 💾 Storage Management
- **File Browser**: Quick access to screenshots and analysis folders
- **Usage Analytics**: Understand your storage consumption patterns
- **File Management**: Open individual files directly from the dashboard

## Installation & Setup

1. **Install Dependencies**:
```bash
npm install
```

2. **Set up Environment**:
Make sure you have your `.env` file configured with your Anthropic API key:
```env
ANTHROPIC_API_KEY=your_api_key_here
```

3. **Start ChromaDB Server** (if not already running):
```bash
chroma run --host localhost --port 8000
```

4. **Launch the Desktop App**:
```bash
npm start
```

## Usage

### Starting the Application

Run the desktop app with:
```bash
npm start
```

For development mode (with DevTools):
```bash
npm run dev
```

### Dashboard Overview

The dashboard is organized into several key sections:

1. **Statistics Card**: Shows real-time counts and totals
2. **System Status Card**: Control tracking and monitor system health
3. **Recent Screenshots**: Browse your latest captures
4. **Recent Analysis**: View recent AI analysis results
5. **MCP Integration**: Monitor ChromaDB and Claude Desktop integration
6. **Storage Management**: File system tools and usage information

### Keyboard Shortcuts

- `Ctrl/Cmd + S`: Start tracking
- `Ctrl/Cmd + T`: Stop tracking
- `Ctrl/Cmd + R`: Reload dashboard
- `F12`: Toggle Developer Tools
- `Ctrl/Cmd + Q`: Quit application

### Menu Options

**File Menu**:
- Open Screenshots Folder
- Open Screen History
- Exit

**Tracking Menu**:
- Start Tracking
- Stop Tracking

**View Menu**:
- Reload
- Toggle Developer Tools

## Technical Architecture

### Main Process (`main.js`)
- Handles app lifecycle and window management
- Manages the screen tracking subprocess
- Provides IPC handlers for communication with renderer
- Implements file system operations and statistics gathering

### Renderer Process (`renderer.js`)
- Manages the user interface and user interactions
- Handles real-time updates and status monitoring
- Communicates with main process via IPC
- Provides interactive controls for the tracking system

### UI (`index.html`)
- Modern, responsive dashboard design
- Card-based layout for easy navigation
- Real-time status indicators
- Integrated logging and monitoring

## Features in Detail

### Real-time Monitoring
- **Live Statistics**: Updates every 30 seconds
- **Status Indicators**: Visual feedback for system health
- **Activity Logs**: Real-time output from tracking processes

### Process Management
- **Subprocess Control**: Start/stop tracking without closing the app
- **Error Handling**: Graceful error recovery and user feedback
- **Auto-restart**: Automatic recovery from tracking failures

### File Management
- **Quick Access**: Direct links to screenshots and analysis folders
- **File Browser**: Interactive file listing with metadata
- **Export Options**: Easy access to all captured data

### Integration Features
- **ChromaDB Integration**: Monitor vector store connectivity
- **Claude Desktop**: Configuration management tools
- **MCP Server**: Status monitoring and troubleshooting

## Troubleshooting

### Common Issues

1. **App Won't Start**:
   - Check that Node.js is installed and up to date
   - Verify all dependencies are installed: `npm install`
   - Check for port conflicts (ChromaDB uses port 8000)

2. **Tracking Won't Start**:
   - Ensure you have the required permissions for screen capture
   - Check that your Anthropic API key is configured correctly
   - Verify ChromaDB is running and accessible

3. **No Statistics Showing**:
   - Make sure the screenshots and screenhistory directories exist
   - Check that the tracking system has generated some data
   - Verify file permissions for reading the data directories

4. **ChromaDB Connection Issues**:
   - Ensure ChromaDB server is running: `chroma run --host localhost --port 8000`
   - Check firewall settings for port 8000
   - Verify ChromaDB configuration in the tracking system

### Development

To contribute to the desktop app:

1. **Development Mode**:
```bash
npm run dev
```

2. **Building for Distribution**:
```bash
npm run build
```

3. **Code Structure**:
- `main.js`: Main Electron process
- `renderer.js`: Renderer process (UI logic)
- `index.html`: UI layout and styling
- `package.json`: Dependencies and build configuration

## Security Considerations

- The app requires screen capture permissions
- Network access is needed for ChromaDB connectivity
- File system access is required for screenshot storage
- API keys should be kept secure in environment variables

## Future Enhancements

- **Data Export**: Export statistics and analysis data
- **Custom Themes**: Multiple UI themes and color schemes
- **Notification System**: Desktop notifications for events
- **Plugin System**: Extensible architecture for custom features
- **Cloud Sync**: Optional cloud backup and synchronization
- **Advanced Analytics**: More detailed usage analytics and insights

This desktop application provides a complete control center for your screen tracking system, making it easy to monitor, control, and analyze your digital activity patterns.