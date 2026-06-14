"use client"

import { useEffect, useRef } from 'react'
import { MessageItem } from './message-item'
import { CitationWidget } from './widgets/citation'
import { RetrievalTraceWidget } from './widgets/retrieval-trace'
import { EvaluationWidget } from './widgets/evaluation'

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

  return (
    <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.map((message) => (
        <MessageItem key={message.id} message={message} />
      ))}
      {isStreaming && (
        <div className="flex justify-start">
          <div className="bg-gray-100 dark:bg-gray-800 rounded-lg p-4 max-w-xs lg:max-w-md">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse animation-delay-200" />
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse animation-delay-400" />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}