import React from 'react'
import { useStatus } from '../hooks/useStatus'

export default function StatusIndicator() {
  const { status, error } = useStatus()

  if (error || !status) {
    return (
      <div className="flex items-center gap-2 text-xs">
        <span className="w-2 h-2 rounded-full bg-memex-error" />
        <span className="text-memex-muted">Offline</span>
      </div>
    )
  }

  const isRunning = status.capture_running

  return (
    <div className="flex items-center gap-2 text-xs">
      <span
        className={`w-2 h-2 rounded-full ${
          isRunning ? 'bg-memex-success animate-pulse' : 'bg-memex-muted'
        }`}
      />
      <span className="text-memex-muted">
        {isRunning ? 'Capturing' : 'Stopped'}
      </span>
    </div>
  )
}
