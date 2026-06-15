"use client"

import { useEffect, useRef } from 'react'
import { MessageItem } from './message-item'
import { ChatMessage } from '@/types'
interface MessageListProps {
  messages: ChatMessage[]
  isStreaming?: boolean
}

export function MessageList({ messages, isStreaming }: MessageListProps) {
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  // The active assistant message renders its own streaming state, so only show
  // the standalone typing bubble before that placeholder exists.
  const hasStreamingAssistant = messages.some((m) => m.isStreaming)

  return (
    <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
      {messages.length === 0 && !isStreaming && (
        <div className="flex flex-col items-center justify-center h-full text-center pb-12">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-cyan-500/10 to-violet-500/10 flex items-center justify-center mb-3">
            <svg className="w-6 h-6 text-cyan-400/40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          </div>
          <p className="text-xs text-white/25">Ask a question to start querying RAGLab</p>
        </div>
      )}

      {messages.map((message) => (
        <MessageItem key={message.id} message={message} />
      ))}

      {isStreaming && !hasStreamingAssistant && (
        <div className="flex justify-start pl-10">
          <div className="glass-card px-4 py-3 rounded-2xl rounded-tl-sm">
            <div className="flex items-center space-x-2">
              <div className="w-1.5 h-1.5 rounded-full bg-cyan-400 typing-dot" />
              <div className="w-1.5 h-1.5 rounded-full bg-cyan-400 typing-dot" />
              <div className="w-1.5 h-1.5 rounded-full bg-cyan-400 typing-dot" />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
