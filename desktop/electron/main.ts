import { app, BrowserWindow, ipcMain } from 'electron'
import path from 'node:path'
import { createTray, destroyTray } from './tray'

let mainWindow: BrowserWindow | null = null

const VITE_DEV_SERVER_URL = process.env['VITE_DEV_SERVER_URL']

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1100,
    height: 750,
    minWidth: 800,
    minHeight: 600,
    titleBarStyle: 'hiddenInset',
    backgroundColor: '#0a0a0a',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  if (VITE_DEV_SERVER_URL) {
    mainWindow.loadURL(VITE_DEV_SERVER_URL)
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'))
  }

  mainWindow.on('closed', () => {
    mainWindow = null
  })

  // Hide instead of close when clicking X (tray keeps running)
  mainWindow.on('close', (event) => {
    if (!app.isQuitting) {
      event.preventDefault()
      mainWindow?.hide()
    }
  })
}

app.on('ready', () => {
  createWindow()
  createTray(mainWindow!)
})

app.on('activate', () => {
  if (mainWindow) {
    mainWindow.show()
  } else {
    createWindow()
  }
})

app.on('before-quit', () => {
  (app as any).isQuitting = true
  destroyTray()
})

app.on('window-all-closed', () => {
  // On macOS, keep app running in tray
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

// IPC handlers for renderer
ipcMain.handle('get-api-url', () => {
  return 'http://localhost:8082'
})
