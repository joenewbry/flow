import { useState, useEffect } from 'react'
import { StatsData } from '../api/types'
import { getStats } from '../api/client'

export function useStats(pollInterval = 30000) {
  const [stats, setStats] = useState<StatsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refresh = async () => {
    const res = await getStats()
    if (res.success && res.data) {
      setStats(res.data)
      setError(null)
    } else {
      setError(res.error || 'Failed to fetch stats')
    }
    setLoading(false)
  }

  useEffect(() => {
    refresh()
    const interval = setInterval(refresh, pollInterval)
    return () => clearInterval(interval)
  }, [pollInterval])

  return { stats, loading, error, refresh }
}
