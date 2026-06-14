"use client"

import { useState, useRef, useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { MessageList } from '@/components/message-list'
import { Composer } from '@/components/composer'
import { useChat } from '@/hooks/use-chat'
import { RAGResult } from '@/types'

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const queryClient = useQueryClient()

  const handleSendMessage = async (content: string, pipeline?: string) => {
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setIsStreaming(true)

    try {
      // Use the existing backend API
      const response = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: content,
          config: pipeline ? `configs/${pipeline}.yaml` : 'configs/naive.yaml',
          ingest_path: 'examples/docs',
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to get response')
      }

      const result: RAGResult = await response.json()

      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: result.answer,
        timestamp: new Date(),
        sources: result.context_texts,
        metrics: result.metrics,
      }

      setMessages(prev => [...prev, assistantMessage])

      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['experiments'] })
    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
        isError: true,
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsStreaming(false)
    }
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex-1 flex flex-col overflow-hidden">
        <MessageList messages={messages} isStreaming={isStreaming} />
      </div>
      <Composer
        onSend={handleSendMessage}
        isLoading={isStreaming}
        placeholder="Ask about RAGLab architectures, embeddings, or evaluation..."
      />
    </div>
  )
}

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  sources?: string[]
  metrics?: any
  isError?: boolean
}