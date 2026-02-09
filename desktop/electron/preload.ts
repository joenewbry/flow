import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('memexAPI', {
  getApiUrl: () => ipcRenderer.invoke('get-api-url'),
})
