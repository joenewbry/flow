import { Tray, Menu, nativeImage, app, BrowserWindow, shell } from 'electron'
import path from 'node:path'
import { exec } from 'node:child_process'

let tray: Tray | null = null

export function createTray(mainWindow: BrowserWindow) {
  // Create a simple tray icon (16x16 template image)
  const icon = nativeImage.createFromDataURL(
    'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAbwAAAG8B8aLcQwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAABhSURBVDiN7dExDoAgEETRPxfx/qdRC+1QG2IhGhe3cJqZYjKTAH9URVVuaO4OM/sGGIGSKoC1Bg9gkfS8AUbg0AXYJe27AJek/RNgkvTqArSSti5gkFT+BLD3n9n/+gI7eRYhCW2U/QAAAABJRU5ErkJggg=='
  )
  icon.setTemplateImage(true)

  tray = new Tray(icon)
  tray.setToolTip('Memex')

  const updateMenu = (isCapturing: boolean = false) => {
    const contextMenu = Menu.buildFromTemplate([
      {
        label: 'Open Memex',
        click: () => mainWindow.show(),
      },
      { type: 'separator' },
      {
        label: isCapturing ? 'Stop Capture' : 'Start Capture',
        click: () => {
          const cmd = isCapturing ? 'memex stop' : 'memex start'
          exec(cmd, (error) => {
            if (!error) {
              updateMenu(!isCapturing)
            }
          })
        },
      },
      { type: 'separator' },
      {
        label: 'Quit',
        click: () => {
          (app as any).isQuitting = true
          app.quit()
        },
      },
    ])

    tray?.setContextMenu(contextMenu)
  }

  // Check initial capture status
  exec('pgrep -f "refinery/run.py"', (error) => {
    updateMenu(!error)
  })

  tray.on('click', () => {
    mainWindow.show()
  })
}

export function destroyTray() {
  if (tray) {
    tray.destroy()
    tray = null
  }
}
