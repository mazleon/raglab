"use client"

import { useCallback, useRef, useState } from 'react'
import type { ChatMessage, RAGContext, RAGMetrics, TrajectoryStep } from '@/types'

export interface SendOptions {
  query: string
  pipeline: string
  overrides?: Record<string, unknown>
  conversationId?: string | null
}

interface ParsedEvent {
  event: string
  data: Record<string, unknown>
}

function parseSSEBlock(block: string): ParsedEvent | null {
  let event = 'message'
  const dataLines: string[] = []
  for (const line of block.split('\n')) {
    if (line.startsWith('event:')) event = line.slice(6).trim()
    else if (line.startsWith('data:')) dataLines.push(line.slice(5).trim())
  }
  if (dataLines.length === 0) return null
  try {
    return { event, data: JSON.parse(dataLines.join('\n')) }
  } catch {
    return null
  }
}

/**
 * Streaming chat controller. Owns the message list, fires a request to the SSE
 * BFF, and folds each event (trace / delta / sources / metrics) into the active
 * assistant message for a live, incremental render.
 */
export function useChatStream(onNewConversation?: (id: string) => void) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const abortRef = useRef<AbortController | null>(null)

  const patchAssistant = useCallback((id: string, patch: Partial<ChatMessage>) => {
    setMessages((prev) =>
      prev.map((m) => (m.id === id ? { ...m, ...patch } : m)),
    )
  }, [])

  const stop = useCallback(() => {
    abortRef.current?.abort()
    setIsStreaming(false)
  }, [])

  const send = useCallback(
    async ({ query, pipeline, overrides, conversationId }: SendOptions) => {
      const userMsg: ChatMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: query,
        timestamp: new Date(),
      }
      const assistantId = `assistant-${Date.now()}`
      const assistantMsg: ChatMessage = {
        id: assistantId,
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        trajectory: [],
        isStreaming: true,
      }
      setMessages((prev) => [...prev, userMsg, assistantMsg])
      setIsStreaming(true)

      const controller = new AbortController()
      abortRef.current = controller

      try {
        const res = await fetch('/api/chat/stream', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query,
            pipeline,
            overrides: overrides ?? {},
            conversation_id: conversationId ?? null,
          }),
          signal: controller.signal,
        })

        if (!res.ok || !res.body) {
          const detail = await res.text().catch(() => '')
          throw new Error(detail || `request failed (${res.status})`)
        }

        const reader = res.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''
        let answer = ''
        const trajectory: TrajectoryStep[] = []

        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          buffer += decoder.decode(value, { stream: true })
          const blocks = buffer.split('\n\n')
          buffer = blocks.pop() ?? ''
          for (const block of blocks) {
            const parsed = parseSSEBlock(block)
            if (!parsed) continue
            const { event, data } = parsed
            if (event === 'meta') {
              const cid = data.conversation_id as string | undefined
              if (cid && !conversationId) onNewConversation?.(cid)
            } else if (event === 'trace') {
              trajectory.push({ name: String(data.name), detail: data.detail as string })
              patchAssistant(assistantId, { trajectory: [...trajectory] })
            } else if (event === 'delta') {
              answer += String(data.text ?? '')
              patchAssistant(assistantId, { content: answer })
            } else if (event === 'sources') {
              patchAssistant(assistantId, { sources: data.contexts as RAGContext[] })
            } else if (event === 'metrics') {
              patchAssistant(assistantId, { metrics: data as unknown as RAGMetrics })
            } else if (event === 'error') {
              patchAssistant(assistantId, {
                content: `⚠️ ${data.detail ?? 'Something went wrong.'}`,
                isError: true,
                isStreaming: false,
              })
            }
          }
        }
        patchAssistant(assistantId, { isStreaming: false })
      } catch (err) {
        if ((err as Error).name === 'AbortError') {
          patchAssistant(assistantId, { isStreaming: false })
        } else {
          patchAssistant(assistantId, {
            content: `⚠️ ${(err as Error).message || 'Failed to reach the server.'}`,
            isError: true,
            isStreaming: false,
          })
        }
      } finally {
        setIsStreaming(false)
        abortRef.current = null
      }
    },
    [onNewConversation, patchAssistant],
  )

  return { messages, setMessages, isStreaming, send, stop }
}
