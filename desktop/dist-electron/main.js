"use strict";
const electron = require("electron");
const path = require("node:path");
const node_child_process = require("node:child_process");
let tray = null;
function createTray(mainWindow2) {
  const icon = electron.nativeImage.createFromDataURL(
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAbwAAAG8B8aLcQwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAABhSURBVDiN7dExDoAgEETRPxfx/qdRC+1QG2IhGhe3cJqZYjKTAH9URVVuaO4OM/sGGIGSKoC1Bg9gkfS8AUbg0AXYJe27AJek/RNgkvTqArSSti5gkFT+BLD3n9n/+gI7eRYhCW2U/QAAAABJRU5ErkJggg=="
  );
  icon.setTemplateImage(true);
  tray = new electron.Tray(icon);
  tray.setToolTip("Memex");
  const updateMenu = (isCapturing = false) => {
    const contextMenu = electron.Menu.buildFromTemplate([
      {
        label: "Open Memex",
        click: () => mainWindow2.show()
      },
      { type: "separator" },
      {
        label: isCapturing ? "Stop Capture" : "Start Capture",
        click: () => {
          const cmd = isCapturing ? "memex stop" : "memex start";
          node_child_process.exec(cmd, (error) => {
            if (!error) {
              updateMenu(!isCapturing);
            }
          });
        }
      },
      { type: "separator" },
      {
        label: "Quit",
        click: () => {
          electron.app.isQuitting = true;
          electron.app.quit();
        }
      }
    ]);
    tray == null ? void 0 : tray.setContextMenu(contextMenu);
  };
  node_child_process.exec('pgrep -f "refinery/run.py"', (error) => {
    updateMenu(!error);
  });
  tray.on("click", () => {
    mainWindow2.show();
  });
}
function destroyTray() {
  if (tray) {
    tray.destroy();
    tray = null;
  }
}
let mainWindow = null;
const VITE_DEV_SERVER_URL = process.env["VITE_DEV_SERVER_URL"];
function createWindow() {
  mainWindow = new electron.BrowserWindow({
    width: 1100,
    height: 750,
    minWidth: 800,
    minHeight: 600,
    titleBarStyle: "hiddenInset",
    backgroundColor: "#0a0a0a",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false
    }
  });
  if (VITE_DEV_SERVER_URL) {
    mainWindow.loadURL(VITE_DEV_SERVER_URL);
  } else {
    mainWindow.loadFile(path.join(__dirname, "../dist/index.html"));
  }
  mainWindow.on("closed", () => {
    mainWindow = null;
  });
  mainWindow.on("close", (event) => {
    if (!electron.app.isQuitting) {
      event.preventDefault();
      mainWindow == null ? void 0 : mainWindow.hide();
    }
  });
}
electron.app.on("ready", () => {
  createWindow();
  createTray(mainWindow);
});
electron.app.on("activate", () => {
  if (mainWindow) {
    mainWindow.show();
  } else {
    createWindow();
  }
});
electron.app.on("before-quit", () => {
  electron.app.isQuitting = true;
  destroyTray();
});
electron.app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    electron.app.quit();
  }
});
electron.ipcMain.handle("get-api-url", () => {
  return "http://localhost:8082";
});
