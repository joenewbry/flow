const { app, BrowserWindow, ipcMain, Menu, dialog, shell } = require('electron');
const path = require('path');
const { promises: fs } = require('fs');
const { spawn } = require('child_process');
const dotenv = require('dotenv');

// __dirname is available in CommonJS by default

// Load environment variables
dotenv.config();

let mainWindow;
let trackingProcess = null;
let isTracking = false;

// Create the main application window
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      enableRemoteModule: true
    },
    icon: path.join(__dirname, 'assets', 'icon.png'),
    title: 'Screen Tracker Dashboard'
  });

  // Load the app
  mainWindow.loadFile('index.html');

  // Open DevTools in development
  if (process.argv.includes('--dev')) {
    mainWindow.webContents.openDevTools();
  }

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
    if (trackingProcess) {
      trackingProcess.kill();
    }
  });

  // Create menu
  createMenu();
}

// Create application menu
function createMenu() {
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'Open Screenshots Folder',
          click: () => {
            shell.openPath(path.join(__dirname, 'screenshots'));
          }
        },
        {
          label: 'Open Screen History',
          click: () => {
            shell.openPath(path.join(__dirname, 'screenhistory'));
          }
        },
        { type: 'separator' },
        {
          label: 'Exit',
          accelerator: 'CmdOrCtrl+Q',
          click: () => {
            app.quit();
          }
        }
      ]
    },
    {
      label: 'Tracking',
      submenu: [
        {
          label: 'Start Tracking',
          accelerator: 'CmdOrCtrl+S',
          click: () => {
            startTracking();
          }
        },
        {
          label: 'Stop Tracking',
          accelerator: 'CmdOrCtrl+T',
          click: () => {
            stopTracking();
          }
        }
      ]
    },
    {
      label: 'View',
      submenu: [
        {
          label: 'Reload',
          accelerator: 'CmdOrCtrl+R',
          click: () => {
            mainWindow.reload();
          }
        },
        {
          label: 'Toggle Developer Tools',
          accelerator: 'F12',
          click: () => {
            mainWindow.webContents.toggleDevTools();
          }
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

// Start tracking process
function startTracking() {
  if (trackingProcess) {
    return;
  }

  try {
    trackingProcess = spawn('node', ['chroma-track-cjs.js'], {
      stdio: 'pipe',
      cwd: __dirname
    });

    trackingProcess.stdout.on('data', (data) => {
      console.log(`Tracking stdout: ${data}`);
      if (mainWindow) {
        mainWindow.webContents.send('tracking-output', data.toString());
      }
    });

    trackingProcess.stderr.on('data', (data) => {
      console.error(`Tracking stderr: ${data}`);
      if (mainWindow) {
        mainWindow.webContents.send('tracking-error', data.toString());
      }
    });

    trackingProcess.on('close', (code) => {
      console.log(`Tracking process exited with code ${code}`);
      trackingProcess = null;
      isTracking = false;
      if (mainWindow) {
        mainWindow.webContents.send('tracking-stopped');
      }
    });

    isTracking = true;
    if (mainWindow) {
      mainWindow.webContents.send('tracking-started');
    }
  } catch (error) {
    console.error('Error starting tracking:', error);
    if (mainWindow) {
      mainWindow.webContents.send('tracking-error', error.message);
    }
  }
}

// Stop tracking process
function stopTracking() {
  if (trackingProcess) {
    trackingProcess.kill();
    trackingProcess = null;
    isTracking = false;
    if (mainWindow) {
      mainWindow.webContents.send('tracking-stopped');
    }
  }
}

// Get statistics about screenshots and analysis
async function getStats() {
  try {
    const screenshotsDir = path.join(__dirname, 'screenshots');
    const screenhistoryDir = path.join(__dirname, 'screenhistory');
    
    let screenshots = [];
    let analysisFiles = [];
    let totalSize = 0;
    let totalWords = 0;
    let totalCharacters = 0;

    // Get screenshot files
    try {
      const screenshotFiles = await fs.readdir(screenshotsDir);
      for (const file of screenshotFiles) {
        const filePath = path.join(screenshotsDir, file);
        const stats = await fs.stat(filePath);
        screenshots.push({
          name: file,
          size: stats.size,
          created: stats.mtime
        });
        totalSize += stats.size;
      }
    } catch (error) {
      console.log('Screenshots directory not found or empty');
    }

    // Get analysis files
    try {
      const analysisFileList = await fs.readdir(screenhistoryDir);
      for (const file of analysisFileList.filter(f => f.endsWith('.json'))) {
        const filePath = path.join(screenhistoryDir, file);
        const stats = await fs.stat(filePath);
        const content = await fs.readFile(filePath, 'utf-8');
        
        let wordCount = 0;
        let charCount = 0;
        
        try {
          const analysis = JSON.parse(content);
          if (analysis.extracted_text) {
            const text = analysis.extracted_text;
            wordCount = text.split(/\s+/).filter(word => word.length > 0).length;
            charCount = text.length;
            totalWords += wordCount;
            totalCharacters += charCount;
          }
        } catch (parseError) {
          console.warn(`Could not parse analysis file ${file}`);
        }
        
        analysisFiles.push({
          name: file,
          size: stats.size,
          created: stats.mtime,
          wordCount,
          charCount
        });
        totalSize += stats.size;
      }
    } catch (error) {
      console.log('Screen history directory not found or empty');
    }

    return {
      screenshots: screenshots.length,
      analysisFiles: analysisFiles.length,
      totalSize,
      totalWords,
      totalCharacters,
      recentScreenshots: screenshots.slice(-10),
      recentAnalysis: analysisFiles.slice(-10)
    };
  } catch (error) {
    console.error('Error getting stats:', error);
    return {
      screenshots: 0,
      analysisFiles: 0,
      totalSize: 0,
      totalWords: 0,
      totalCharacters: 0,
      recentScreenshots: [],
      recentAnalysis: []
    };
  }
}

// IPC handlers
ipcMain.handle('get-stats', async () => {
  return await getStats();
});

ipcMain.handle('start-tracking', async () => {
  startTracking();
  return isTracking;
});

ipcMain.handle('stop-tracking', async () => {
  stopTracking();
  return isTracking;
});

ipcMain.handle('get-tracking-status', async () => {
  return isTracking;
});

ipcMain.handle('open-screenshot', async (event, filename) => {
  const filePath = path.join(__dirname, 'screenshots', filename);
  shell.openPath(filePath);
});

ipcMain.handle('open-analysis', async (event, filename) => {
  const filePath = path.join(__dirname, 'screenhistory', filename);
  shell.openPath(filePath);
});

ipcMain.handle('check-chroma-status', async () => {
  try {
    // Simple check to see if ChromaDB is accessible
    const response = await fetch('http://localhost:8000/api/v1/heartbeat');
    return response.ok;
  } catch (error) {
    return false;
  }
});

// App event handlers
app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  if (trackingProcess) {
    trackingProcess.kill();
  }
});

// Handle app closing
app.on('will-quit', (event) => {
  if (trackingProcess) {
    event.preventDefault();
    trackingProcess.kill();
    setTimeout(() => {
      app.quit();
    }, 1000);
  }
});