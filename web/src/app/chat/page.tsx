"use client"

import { useCallback, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { MessageList } from '@/components/message-list'
import { Composer } from '@/components/composer'
import { ModelSelector } from '@/components/model-selector'
import { ConversationSidebar } from '@/components/conversation-sidebar'
import { useConfig } from '@/hooks/use-config'
import { useChatStream } from '@/hooks/use-chat-stream'
import { cn } from '@/lib/utils'
import type { ChatMessage, StoredMessage } from '@/types'

function providerColor(provider?: string): string {
  switch (provider) {
    case 'openai': return 'bg-emerald-500'
    case 'openrouter': return 'bg-violet-500'
    case 'gemini': return 'bg-blue-500'
    case 'echo': return 'bg-amber-500'
    case 'cohere': return 'bg-rose-500'
    case 'hashing': return 'bg-cyan-500'
    default: return 'bg-slate-400/50'
  }
}

const pipelineColorMap: Record<string, string> = {
  naive: 'bg-cyan-400',
  hybrid: 'bg-emerald-400',
  agentic: 'bg-violet-400',
}

export default function ChatPage() {
  const queryClient = useQueryClient()
  const { data: config } = useConfig()

  const [activeId, setActiveId] = useState<string | null>(null)
  const [showConfig, setShowConfig] = useState(false)
  const [selectedPipeline, setSelectedPipeline] = useState('naive')
  const [selectedModel, setSelectedModel] = useState('echo')
  const [selectedEmbedding, setSelectedEmbedding] = useState('hashing')

  const onNewConversation = useCallback((id: string) => {
    setActiveId(id)
    queryClient.invalidateQueries({ queryKey: ['conversations'] })
  }, [queryClient])

  const { messages, setMessages, isStreaming, send, stop } = useChatStream(onNewConversation)

  const buildOverrides = useCallback(() => {
    const model = config?.models.find((m) => m.id === selectedModel)
    const embed = config?.embeddings.find((e) => e.id === selectedEmbedding)
    const overrides: Record<string, unknown> = {}
    if (model) {
      overrides.llm = { provider: model.provider, model: model.provider === 'echo' ? null : model.id }
    }
    if (embed) overrides.embedding = { name: embed.id }
    return overrides
  }, [config, selectedModel, selectedEmbedding])

  const handleSend = useCallback((content: string) => {
    void send({
      query: content,
      pipeline: selectedPipeline,
      overrides: buildOverrides(),
      conversationId: activeId,
    })
  }, [send, selectedPipeline, buildOverrides, activeId])

  const handleNew = useCallback(() => {
    if (isStreaming) stop()
    setActiveId(null)
    setMessages([])
  }, [isStreaming, stop, setMessages])

  const handleSelect = useCallback(async (id: string) => {
    if (isStreaming) stop()
    setActiveId(id)
    setMessages([])
    const res = await fetch(`/api/conversations/${id}`, { cache: 'no-store' })
    if (!res.ok) return
    const data = await res.json()
    const loaded: ChatMessage[] = (data.messages ?? []).map((m: StoredMessage) => ({
      id: m.id,
      role: m.role,
      content: m.content,
      timestamp: new Date(m.created_at),
      sources: m.metadata?.sources,
      metrics: m.metadata?.metrics,
    }))
    setMessages(loaded)
  }, [isStreaming, stop, setMessages])

  const pipelineInfo = config?.pipelines.find((p) => p.id === selectedPipeline)
  const modelInfo = config?.models.find((m) => m.id === selectedModel)
  const embedInfo = config?.embeddings.find((e) => e.id === selectedEmbedding)

  return (
    <div className="h-full flex -m-6">
      <ConversationSidebar activeId={activeId} onSelect={handleSelect} onNew={handleNew} />

      <div className="flex-1 flex flex-col min-w-0">
        {/* Config status bar */}
        <div className="flex-shrink-0 border-b border-base px-4 py-1.5 surface backdrop-blur-sm">
          <div className="max-w-4xl mx-auto flex items-center justify-between">
            <div className="flex items-center space-x-2.5">
              <div className="flex items-center space-x-1">
                <span className={cn('w-1 h-1 rounded-full', pipelineColorMap[selectedPipeline] || 'bg-cyan-400')} />
                <span className="text-[10px] text-subtle">{pipelineInfo?.name || 'Naive RAG'}</span>
              </div>
              <span className="text-subtle">/</span>
              <div className="flex items-center space-x-1">
                <span className={cn('w-1 h-1 rounded-full', providerColor(modelInfo?.provider))} />
                <span className="text-[10px] text-subtle">{modelInfo?.name?.split(' ')[0] || 'Echo'}</span>
              </div>
              <span className="text-subtle hidden sm:inline">/</span>
              <div className="items-center space-x-1 hidden sm:flex">
                <span className={cn('w-1 h-1 rounded-full', providerColor(embedInfo?.provider))} />
                <span className="text-[10px] text-subtle">{embedInfo?.name?.split(' ')[0] || 'Hashing'}</span>
              </div>
            </div>

            <button
              onClick={() => setShowConfig(!showConfig)}
              className={cn(
                'flex items-center space-x-1 px-2 py-0.5 rounded-md transition-all text-[10px]',
                showConfig ? 'bg-cyan-500/10 text-cyan-300/80' : 'text-subtle hover:text-muted surface-hover',
              )}
            >
              <svg className="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 11-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 11-2.83-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 112.83-2.83l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 112.83 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z" />
              </svg>
              <span>Configure</span>
            </button>
          </div>

          {showConfig && (
            <div className="max-w-4xl mx-auto mt-2 pt-2.5 border-t border-base animate-slide-up">
              <ModelSelector
                selectedModel={selectedModel}
                selectedEmbedding={selectedEmbedding}
                selectedPipeline={selectedPipeline}
                onModelChange={setSelectedModel}
                onEmbeddingChange={setSelectedEmbedding}
                onPipelineChange={setSelectedPipeline}
              />
            </div>
          )}
        </div>

        <div className="flex-1 flex flex-col overflow-hidden">
          <MessageList messages={messages} isStreaming={isStreaming} />
        </div>

        <Composer
          onSend={handleSend}
          isLoading={isStreaming}
          onStop={stop}
          placeholder="Ask about your documents, RAG architectures, or evaluations…"
          pipeline={selectedPipeline}
          pipelineName={pipelineInfo?.name}
          pipelineColor={pipelineColorMap[selectedPipeline]}
        />
      </div>
    </div>
  )
}
