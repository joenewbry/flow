import { useState, useEffect } from 'react'
import { StatusData } from '../api/types'
import { getStatus } from '../api/client'

export function useStatus(pollInterval = 10000) {
  const [status, setStatus] = useState<StatusData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refresh = async () => {
    const res = await getStatus()
    if (res.success && res.data) {
      setStatus(res.data)
      setError(null)
    } else {
      setError(res.error || 'Failed to fetch status')
    }
    setLoading(false)
  }

  useEffect(() => {
    refresh()
    const interval = setInterval(refresh, pollInterval)
    return () => clearInterval(interval)
  }, [pollInterval])

  return { status, loading, error, refresh }
}
