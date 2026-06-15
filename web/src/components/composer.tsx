"use client"

import { useState, useRef, useEffect, type FormEvent, type KeyboardEvent } from 'react'
import { cn } from '@/lib/utils'

interface ComposerProps {
  onSend: (content: string) => void
  isLoading?: boolean
  onStop?: () => void
  placeholder?: string
  pipeline?: string
  pipelineName?: string
  pipelineColor?: string
}

export function Composer({ onSend, isLoading, onStop, placeholder, pipeline: _pipeline, pipelineName, pipelineColor }: ComposerProps) {
  const [input, setInput] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    const ta = textareaRef.current
    if (ta) {
      ta.style.height = 'auto'
      ta.style.height = Math.min(ta.scrollHeight, 160) + 'px'
    }
  }, [input])

  useEffect(() => {
    if (!isLoading && textareaRef.current) textareaRef.current.focus()
  }, [isLoading])

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return
    onSend(input.trim())
    setInput('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit(e) }
  }

  return (
    <div className="border-t border-white/[0.06] bg-black/40 backdrop-blur-xl px-4 py-3">
      <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
        <div className="flex items-end space-x-2">
          {/* Pipeline badge — small inline indicator */}
          <div className="flex items-center space-x-1.5 px-2.5 py-2 border border-white/[0.06] rounded-lg bg-white/[0.03] flex-shrink-0">
            <span className={cn('w-1.5 h-1.5 rounded-full', pipelineColor || 'bg-cyan-400')} />
            <span className="text-[10px] text-white/40 font-medium">{pipelineName || 'Naive'}</span>
          </div>

          {/* Textarea */}
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={placeholder || 'Ask about RAGLab...'}
              rows={1}
              disabled={isLoading}
              className={cn(
                'w-full px-3.5 py-2 pr-10 border border-white/[0.06] rounded-lg',
                'bg-white/[0.03] text-white/85 placeholder:text-white/20',
                'focus:outline-none focus:border-cyan-500/25 focus:bg-white/[0.05]',
                'transition-all resize-none min-h-[36px] max-h-[160px] text-sm',
                'disabled:opacity-50'
              )}
            />
          </div>

          {/* Send / Stop button */}
          {isLoading && onStop ? (
            <button
              type="button"
              onClick={onStop}
              className="flex items-center justify-center w-[36px] h-[36px] rounded-lg flex-shrink-0 bg-rose-500/80 text-white hover:bg-rose-500 transition-all active:scale-95"
              title="Stop generating"
            >
              <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
                <rect x="6" y="6" width="12" height="12" rx="2" />
              </svg>
            </button>
          ) : (
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className={cn(
                'flex items-center justify-center w-[36px] h-[36px] rounded-lg font-medium transition-all duration-200 flex-shrink-0',
                input.trim() && !isLoading
                  ? 'bg-gradient-to-r from-cyan-500 to-violet-600 text-white hover:shadow-lg hover:shadow-cyan-500/20 active:scale-95'
                  : 'bg-white/[0.04] text-white/20 cursor-not-allowed'
              )}
            >
              {isLoading ? (
                <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m6.59 5.564a8.002 8.002 0 01-3.97 2.12M6.3 15.568a8.006 8.006 0 01-3.97-2.12m12.435-5.716a4 4 0 00-5.646-5.646M9 18l3-3m0 0l3-3m-3 3v12h-3" />
                </svg>
              ) : (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M12 5l7 7-7 7" />
                </svg>
              )}
            </button>
          )}
        </div>

        <div className="flex items-center justify-between mt-1.5 px-1">
          <span className="text-[9px] text-white/20">
            <kbd className="px-1 py-0.5 rounded bg-white/[0.05] font-mono text-[8px] text-white/30">Enter</kbd>
            <span className="mx-1">send ·</span>
            <kbd className="px-1 py-0.5 rounded bg-white/[0.05] font-mono text-[8px] text-white/30">Shift+Enter</kbd>
            <span className="ml-0.5">new line</span>
          </span>
          <span className="text-[9px] text-white/20">
            {pipelineName || 'Naive'}
          </span>
        </div>
      </form>
    </div>
  )
}
