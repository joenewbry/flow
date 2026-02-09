import React, { useState, useRef, useEffect } from 'react'
import ChatMessage from '../components/ChatMessage'
import { callTool } from '../api/client'
import { ChatMessage as ChatMessageType } from '../api/types'

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessageType[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async () => {
    const text = input.trim()
    if (!text || loading) return

    setInput('')
    setMessages((prev) => [...prev, { role: 'user', content: text }])
    setLoading(true)

    try {
      // Use the search tool to find relevant data
      const searchResult = await callTool('search-screenshots', { query: text, limit: 5 })

      // Build a response from the tool results
      let response = ''
      if (searchResult.success && searchResult.result) {
        const result = searchResult.result
        if (result.total_results === 0 || result.error) {
          response = `I searched your screen captures for "${text}" but didn't find any matches. Try a different query or make sure Memex is running and capturing data.`
        } else {
          response = `Found ${result.total_results ?? 'some'} results for "${text}":\n\n`
          const results = result.results || []
          for (const r of results.slice(0, 5)) {
            const time = r.timestamp ? new Date(r.timestamp).toLocaleString() : 'Unknown time'
            const preview = (r.text || '').slice(0, 200)
            response += `**${time}** (${r.screen_name || 'screen'})\n${preview}...\n\n`
          }
        }
      } else {
        response = 'Could not connect to the Memex server. Make sure it is running on port 8082.'
      }

      setMessages((prev) => [...prev, { role: 'assistant', content: response }])
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Something went wrong. Check that the Memex HTTP server is running.' },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 h-full flex flex-col">
      <h1 className="text-lg font-semibold mb-4">Chat</h1>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto mb-4 space-y-1">
        {messages.length === 0 && (
          <div className="text-memex-muted text-sm py-12 text-center">
            Ask Memex anything about your screen history.
            <br />
            <span className="text-xs">
              Try: "What was I working on this morning?" or "Find emails about project X"
            </span>
          </div>
        )}
        {messages.map((msg, i) => (
          <ChatMessage key={i} role={msg.role} content={msg.content} />
        ))}
        {loading && (
          <div className="flex justify-start mb-3">
            <div className="bg-memex-surface border border-memex-border rounded-lg px-4 py-2.5 text-sm text-memex-muted">
              Searching...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Ask about your screen history..."
          className="flex-1 bg-memex-surface border border-memex-border rounded-lg px-4 py-2.5 text-sm text-memex-text placeholder:text-memex-muted focus:outline-none focus:border-memex-primary"
          disabled={loading}
        />
        <button
          onClick={sendMessage}
          disabled={loading || !input.trim()}
          className="bg-memex-primary/20 text-memex-primary px-4 py-2.5 rounded-lg text-sm font-medium hover:bg-memex-primary/30 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          Send
        </button>
      </div>
    </div>
  )
}
