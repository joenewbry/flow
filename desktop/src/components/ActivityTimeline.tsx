import React, { useState } from 'react'
import { ActivityEntry } from '../api/types'

interface ActivityTimelineProps {
  entries: ActivityEntry[]
}

function TimelineEntry({ entry }: { entry: ActivityEntry }) {
  const [expanded, setExpanded] = useState(false)
  const time = new Date(entry.timestamp).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  })
  const preview = entry.text?.slice(0, 120) || 'No text captured'

  return (
    <div
      className="border-l-2 border-memex-border pl-4 py-2 hover:border-memex-primary cursor-pointer transition-colors"
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-center gap-2 text-xs text-memex-muted mb-1">
        <span>{time}</span>
        <span className="bg-memex-border px-1.5 py-0.5 rounded text-[10px]">
          {entry.screen_name}
        </span>
        <span>{entry.word_count} words</span>
      </div>
      <div className="text-sm text-memex-text">
        {expanded ? entry.text : preview + (entry.text?.length > 120 ? '...' : '')}
      </div>
    </div>
  )
}

export default function ActivityTimeline({ entries }: ActivityTimelineProps) {
  if (!entries || entries.length === 0) {
    return (
      <div className="text-memex-muted text-sm py-8 text-center">
        No activity for this period.
      </div>
    )
  }

  // Group entries by hour
  const grouped = entries.reduce<Record<string, ActivityEntry[]>>((acc, entry) => {
    const hour = new Date(entry.timestamp).toLocaleTimeString([], {
      hour: '2-digit',
      minute: undefined,
    })
    if (!acc[hour]) acc[hour] = []
    acc[hour].push(entry)
    return acc
  }, {})

  return (
    <div className="space-y-6">
      {Object.entries(grouped).map(([hour, items]) => (
        <div key={hour}>
          <div className="text-xs font-medium text-memex-muted uppercase mb-2">
            {hour}
          </div>
          <div className="space-y-1">
            {items.map((entry, i) => (
              <TimelineEntry key={i} entry={entry} />
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
