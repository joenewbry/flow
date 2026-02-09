import { ApiResponse, StatsData, ActivityData, StatusData, ToolCallResponse } from './types'

const API_BASE = 'http://localhost:8082'

async function fetchApi<T>(path: string, options?: RequestInit): Promise<ApiResponse<T>> {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    })
    if (!res.ok) {
      return { success: false, error: `HTTP ${res.status}` }
    }
    return await res.json()
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : 'Network error' }
  }
}

export async function getStats(): Promise<ApiResponse<StatsData>> {
  return fetchApi<StatsData>('/api/stats')
}

export async function getActivity(start: string, end: string, limit = 50): Promise<ApiResponse<ActivityData>> {
  const params = new URLSearchParams({ start, end, limit: String(limit) })
  return fetchApi<ActivityData>(`/api/activity?${params}`)
}

export async function getStatus(): Promise<ApiResponse<StatusData>> {
  return fetchApi<StatusData>('/api/status')
}

export async function callTool(tool: string, args: Record<string, any> = {}): Promise<ToolCallResponse> {
  try {
    const res = await fetch(`${API_BASE}/tools/call`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tool, arguments: args }),
    })
    return await res.json()
  } catch (err) {
    return { success: false, tool, result: null }
  }
}
