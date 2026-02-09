import { useState, useEffect } from 'react'
import { ActivityData } from '../api/types'
import { getActivity } from '../api/client'

export function useActivity(start: string, end: string, limit = 50, pollInterval = 30000) {
  const [activity, setActivity] = useState<ActivityData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refresh = async () => {
    const res = await getActivity(start, end, limit)
    if (res.success && res.data) {
      setActivity(res.data)
      setError(null)
    } else {
      setError(res.error || 'Failed to fetch activity')
    }
    setLoading(false)
  }

  useEffect(() => {
    refresh()
    const interval = setInterval(refresh, pollInterval)
    return () => clearInterval(interval)
  }, [start, end, limit, pollInterval])

  return { activity, loading, error, refresh }
}
