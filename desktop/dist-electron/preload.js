"use strict";
const electron = require("electron");
electron.contextBridge.exposeInMainWorld("memexAPI", {
  getApiUrl: () => electron.ipcRenderer.invoke("get-api-url")
});
