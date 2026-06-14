"use client"

import { useState } from 'react'
import { cn } from '@/lib/utils'

interface ComposerProps {
  onSend: (content: string, pipeline?: string) => void
  isLoading?: boolean
  placeholder?: string
}

export function Composer({ onSend, isLoading, placeholder }: ComposerProps) {
  const [input, setInput] = useState('')
  const [pipeline, setPipeline] = useState<string | undefined>()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    onSend(input.trim(), pipeline)
    setInput('')
  }

  return (
    <div className="border-t bg-white dark:bg-gray-800 p-4">
      <form onSubmit={handleSubmit} className="flex flex-col space-y-3">
        <div className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={placeholder || 'Type a message...'}
            className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          />

          <select
            value={pipeline || ''}
            onChange={(e) => setPipeline(e.target.value || undefined)}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          >
            <option value="">Default (Naive RAG)</option>
            <option value="hybrid">Hybrid RAG</option>
            <option value="agentic">Agentic RAG</option>
          </select>

          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className={cn(
              'px-4 py-2 rounded-lg font-medium transition-colors',
              'bg-blue-500 hover:bg-blue-600 text-white disabled:bg-gray-300 dark:disabled:bg-gray-600',
              'focus:outline-none focus:ring-2 focus:ring-blue-500'
            )}
          >
            {isLoading ? (
              <svg
                className="w-5 h-5 animate-spin"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m6.59 5.564a8.002 8.002 0 01-3.97 2.12M6.3 15.568a8.006 8.006 0 01-3.97-2.12m12.435-5.716a4 4 0 00-5.646-5.646M9 18l3-3m0 0l3-3m-3 3v12h-3"
                />
              </svg>
            ) : (
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 19l9-9m-9 9l-9-9"
                />
              </svg>
            )}
          </button>
        </div>

        <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
          <span>Press Enter to send</span>
          <span>Use pipeline dropdown to change RAG architecture</span>
        </div>
      </form>
    </div>
  )
}