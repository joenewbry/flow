import React from 'react'
import ReactMarkdown from 'react-markdown'

interface ChatMessageProps {
  role: 'user' | 'assistant'
  content: string
}

export default function ChatMessage({ role, content }: ChatMessageProps) {
  const isUser = role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-3`}>
      <div
        className={`max-w-[80%] rounded-lg px-4 py-2.5 text-sm ${
          isUser
            ? 'bg-memex-primary/20 text-memex-text'
            : 'bg-memex-surface border border-memex-border text-memex-text'
        }`}
      >
        {isUser ? (
          <p>{content}</p>
        ) : (
          <div className="prose prose-invert prose-sm max-w-none [&_p]:mb-2 [&_ul]:mb-2 [&_li]:mb-0.5">
            <ReactMarkdown>{content}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  )
}
