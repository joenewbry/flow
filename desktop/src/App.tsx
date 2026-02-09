import React from 'react'
import { HashRouter, Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import StatsPage from './pages/StatsPage'
import ActivityPage from './pages/ActivityPage'
import ChatPage from './pages/ChatPage'

export default function App() {
  return (
    <HashRouter>
      <div className="flex h-screen bg-memex-bg">
        <Sidebar />
        <main className="flex-1 overflow-hidden">
          {/* Title bar drag region for the main area */}
          <div className="titlebar-drag h-8" />
          <div className="h-[calc(100vh-2rem)] overflow-hidden">
            <Routes>
              <Route path="/" element={<StatsPage />} />
              <Route path="/activity" element={<ActivityPage />} />
              <Route path="/chat" element={<ChatPage />} />
            </Routes>
          </div>
        </main>
      </div>
    </HashRouter>
  )
}
