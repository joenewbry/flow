import React from 'react'
import { NavLink } from 'react-router-dom'
import StatusIndicator from './StatusIndicator'

const navItems = [
  { to: '/', label: 'Stats', icon: '|||' },
  { to: '/activity', label: 'Activity', icon: '...' },
  { to: '/chat', label: 'Chat', icon: '>' },
]

export default function Sidebar() {
  return (
    <div className="w-48 h-screen bg-memex-surface border-r border-memex-border flex flex-col">
      {/* Title bar drag region */}
      <div className="titlebar-drag h-12 flex items-end px-4 pb-2">
        <span className="text-memex-primary font-semibold text-sm titlebar-no-drag">
          MEMEX
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-4 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                isActive
                  ? 'bg-memex-primary/15 text-memex-primary'
                  : 'text-memex-muted hover:text-memex-text hover:bg-memex-border/50'
              }`
            }
          >
            <span className="font-mono text-xs w-4">{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>

      {/* Status footer */}
      <div className="px-4 py-3 border-t border-memex-border">
        <StatusIndicator />
      </div>
    </div>
  )
}
