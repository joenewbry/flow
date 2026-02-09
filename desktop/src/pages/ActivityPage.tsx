import React, { useState } from 'react'
import { useActivity } from '../hooks/useActivity'
import ActivityTimeline from '../components/ActivityTimeline'

function toISODate(date: Date): string {
  return date.toISOString().split('T')[0]
}

export default function ActivityPage() {
  const [selectedDate, setSelectedDate] = useState(toISODate(new Date()))

  const start = `${selectedDate}T00:00:00`
  const end = `${selectedDate}T23:59:59`
  const { activity, loading, error } = useActivity(start, end)

  const goToDate = (offset: number) => {
    const d = new Date(selectedDate)
    d.setDate(d.getDate() + offset)
    setSelectedDate(toISODate(d))
  }

  const entries = activity?.results ?? []

  return (
    <div className="p-6 h-full flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-lg font-semibold">Activity</h1>

        {/* Date navigation */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => goToDate(-1)}
            className="text-memex-muted hover:text-memex-text px-2 py-1 rounded hover:bg-memex-border/50 text-sm"
          >
            &larr; Prev
          </button>
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="bg-memex-surface border border-memex-border rounded px-3 py-1 text-sm text-memex-text"
          />
          <button
            onClick={() => goToDate(1)}
            className="text-memex-muted hover:text-memex-text px-2 py-1 rounded hover:bg-memex-border/50 text-sm"
            disabled={selectedDate >= toISODate(new Date())}
          >
            Next &rarr;
          </button>
        </div>
      </div>

      {/* Timeline */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="text-memex-muted text-sm py-8 text-center">
            Loading activity...
          </div>
        ) : error ? (
          <div className="bg-memex-error/10 border border-memex-error/30 rounded-lg p-4 text-sm text-memex-error">
            {error}
          </div>
        ) : (
          <>
            <div className="text-xs text-memex-muted mb-4">
              {entries.length} captures on {new Date(selectedDate).toLocaleDateString(undefined, {
                weekday: 'long',
                month: 'long',
                day: 'numeric',
              })}
            </div>
            <ActivityTimeline entries={entries} />
          </>
        )}
      </div>
    </div>
  )
}
