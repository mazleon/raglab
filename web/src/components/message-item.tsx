"use client"

import { useState, useMemo } from 'react'
import { ChatMessage } from '@/types'
import { cn } from '@/lib/utils'

interface MessageItemProps {
  message: ChatMessage
}

export function MessageItem({ message }: MessageItemProps) {
  const isUser = message.role === 'user'
  const [isCopied, setIsCopied] = useState(false)

  // Deduplicate sources by source path
  const uniqueSources = useMemo(() => {
    if (!message.sources) return []
    const seen = new Set<string>()
    return message.sources.filter(ctx => {
      const key = ctx.source
      if (seen.has(key)) return false
      seen.add(key)
      return true
    })
  }, [message.sources])

  const handleCopy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setIsCopied(true)
      setTimeout(() => setIsCopied(false), 2000)
    } catch { /* fallback */ }
  }

  return (
    <div className={cn('flex animate-slide-up', isUser ? 'justify-end' : 'justify-start')}>
      <div className={cn('max-w-[88%] lg:max-w-[72%]', !isUser && 'flex items-start space-x-3')}>
        {/* Assistant avatar */}
        {!isUser && (
          <div className="flex-shrink-0 w-7 h-7 rounded-lg bg-gradient-to-br from-cyan-500 to-violet-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 mt-0.5">
            <svg className="w-3.5 h-3.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
        )}

        <div className="flex-1 min-w-0">
          {/* Message bubble */}
          <div className={cn(
            'group relative px-4 py-3 transition-all duration-200',
            isUser
              ? 'bg-gradient-to-r from-cyan-600/80 to-blue-600/80 text-white rounded-2xl rounded-tr-sm'
              : 'glass-card text-primary rounded-2xl rounded-tl-sm'
          )}>
            {/* Copy button — inside bubble, top-right, not overlapping */}
            <button
              onClick={() => handleCopy(message.content)}
              className={cn(
                'absolute top-2 right-2 p-1 rounded-md transition-all duration-200',
                'opacity-0 group-hover:opacity-100 surface-hover',
                isCopied && 'opacity-100'
              )}
              title="Copy message"
            >
              {isCopied ? (
                <svg className="w-3 h-3 text-emerald-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                <svg className={cn('w-3 h-3', isUser ? 'text-muted' : 'text-subtle')} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              )}
            </button>

            {/* Reasoning trajectory (agentic steps) */}
            {!isUser && message.trajectory && message.trajectory.length > 0 && (
              <div className="mb-2.5 flex flex-wrap items-center gap-1">
                {message.trajectory.map((step, i) => (
                  <span
                    key={i}
                    className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-violet-500/10 border border-violet-500/15 text-[9px] font-medium text-violet-400"
                    title={step.detail || step.name}
                  >
                    <span className="w-1 h-1 rounded-full bg-violet-400/70" />
                    {step.name}
                  </span>
                ))}
              </div>
            )}

            {/* Content */}
            <div className="text-sm leading-relaxed whitespace-pre-wrap pr-6">
              {message.content}
              {message.isStreaming && (
                <span className="inline-block w-1.5 h-3.5 ml-0.5 -mb-0.5 bg-cyan-400/70 animate-pulse rounded-sm" />
              )}
              {message.isStreaming && !message.content && (
                <span className="text-subtle text-xs">Thinking…</span>
              )}
            </div>

            {/* Sources — compact chips */}
            {!isUser && uniqueSources.length > 0 && (
              <div className="mt-3 pt-2.5 border-t border-base">
                <div className="flex flex-wrap gap-1.5">
                  {uniqueSources.slice(0, 3).map((ctx, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center space-x-1 px-2 py-1 rounded-md surface border border-base text-[10px] text-muted max-w-full"
                    >
                      <svg className="w-2.5 h-2.5 flex-shrink-0 text-cyan-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <span className="truncate">
                        {ctx.source.split('/').pop() || ctx.source}
                      </span>
                      {ctx.score > 0 && (
                        <span className="text-[9px] text-subtle ml-1">
                          {(ctx.score * 100).toFixed(0)}%
                        </span>
                      )}
                    </span>
                  ))}
                  {uniqueSources.length > 3 && (
                    <span className="inline-flex items-center px-2 py-1 rounded-md surface text-[10px] text-subtle">
                      +{uniqueSources.length - 3} more
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Metrics row — clean horizontal bar */}
          {!isUser && message.metrics && (
            <div className="flex flex-wrap items-center gap-2 mt-1.5 ml-1">
              {message.metrics.latency_ms !== undefined && (
                <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-md surface text-[9px] text-subtle">
                  <svg className="w-2.5 h-2.5 text-cyan-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>{message.metrics.latency_ms.toFixed(0)}ms</span>
                </span>
              )}
              {message.metrics.total_tokens !== undefined && (
                <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-md surface text-[9px] text-subtle">
                  <svg className="w-2.5 h-2.5 text-violet-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                  </svg>
                  <span>{message.metrics.total_tokens.toLocaleString()}</span>
                </span>
              )}
              {message.metrics.usd_cost !== undefined && (
                <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-md surface text-[9px] text-subtle">
                  <svg className="w-2.5 h-2.5 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>${message.metrics.usd_cost.toFixed(4)}</span>
                </span>
              )}
              {message.metrics.retriever_hits !== undefined && (
                <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-md surface text-[9px] text-subtle">
                  <svg className="w-2.5 h-2.5 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>{message.metrics.retriever_hits}</span>
                </span>
              )}
            </div>
          )}

          {/* Timestamp */}
          <div className={cn('flex items-center space-x-1.5 mt-1', isUser ? 'justify-end mr-1' : 'justify-start ml-1')}>
            <span className="text-[9px] text-subtle">
              {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
            {isUser && (
              <svg className="w-2.5 h-2.5 text-cyan-500" fill="currentColor" viewBox="0 0 24 24">
                <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z" />
              </svg>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
