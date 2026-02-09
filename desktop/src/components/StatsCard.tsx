import React from 'react'

interface StatsCardProps {
  label: string
  value: string | number
  subtitle?: string
}

export default function StatsCard({ label, value, subtitle }: StatsCardProps) {
  return (
    <div className="bg-memex-surface border border-memex-border rounded-lg p-4">
      <div className="text-xs text-memex-muted uppercase tracking-wide mb-1">
        {label}
      </div>
      <div className="text-2xl font-semibold text-memex-text">
        {typeof value === 'number' ? value.toLocaleString() : value}
      </div>
      {subtitle && (
        <div className="text-xs text-memex-muted mt-1">{subtitle}</div>
      )}
    </div>
  )
}
