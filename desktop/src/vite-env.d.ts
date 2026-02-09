/// <reference types="vite/client" />

interface Window {
  memexAPI: {
    getApiUrl: () => Promise<string>
  }
}
