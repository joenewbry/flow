export interface StatsData {
  total_files?: number
  total_size_bytes?: number
  chromadb_documents?: number
  oldest_file?: string
  newest_file?: string
  [key: string]: any
}

export interface ActivityEntry {
  timestamp: string
  screen_name: string
  text: string
  word_count: number
}

export interface ActivityData {
  total_results?: number
  results?: ActivityEntry[]
  [key: string]: any
}

export interface StatusData {
  capture_running: boolean
  chromadb_connected: boolean
  last_capture: string | null
  uptime: string | null
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
}

export interface ToolCallResponse {
  success: boolean
  tool: string
  result: any
}
