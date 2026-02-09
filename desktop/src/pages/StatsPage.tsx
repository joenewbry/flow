import React from 'react'
import { useStats } from '../hooks/useStats'
import { useStatus } from '../hooks/useStatus'
import StatsCard from '../components/StatsCard'

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`
}

function formatTimeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'Just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

export default function StatsPage() {
  const { stats, loading, error } = useStats()
  const { status } = useStatus()

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full text-memex-muted">
        Loading stats...
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6">
        <h1 className="text-lg font-semibold mb-4">Stats</h1>
        <div className="bg-memex-error/10 border border-memex-error/30 rounded-lg p-4 text-sm text-memex-error">
          Could not connect to Memex server. Make sure the HTTP server is running on port 8082.
        </div>
      </div>
    )
  }

  const totalFiles = stats?.total_files ?? stats?.chromadb_documents ?? 0
  const totalSize = stats?.total_size_bytes ?? 0
  const lastCapture = status?.last_capture

  return (
    <div className="p-6">
      <h1 className="text-lg font-semibold mb-6">Dashboard</h1>

      {/* Primary metrics */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <StatsCard
          label="Total Captures"
          value={totalFiles}
        />
        <StatsCard
          label="Storage Used"
          value={formatBytes(totalSize)}
        />
        <StatsCard
          label="Last Capture"
          value={lastCapture ? formatTimeAgo(lastCapture) : '-'}
          subtitle={lastCapture ? new Date(lastCapture).toLocaleString() : undefined}
        />
      </div>

      {/* ChromaDB info */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <StatsCard
          label="ChromaDB Documents"
          value={stats?.chromadb_documents ?? 0}
        />
        <StatsCard
          label="Capture Status"
          value={status?.capture_running ? 'Running' : 'Stopped'}
          subtitle={status?.chromadb_connected ? 'ChromaDB connected' : 'ChromaDB disconnected'}
        />
      </div>

      {/* Date range */}
      {stats?.oldest_file && (
        <div className="bg-memex-surface border border-memex-border rounded-lg p-4 text-sm text-memex-muted">
          Data range: {new Date(stats.oldest_file).toLocaleDateString()} — {' '}
          {stats.newest_file ? new Date(stats.newest_file).toLocaleDateString() : 'now'}
        </div>
      )}
    </div>
  )
}
