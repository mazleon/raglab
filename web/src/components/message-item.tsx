"use client"

import { ChatMessage } from '@/types'
import { cn } from '@/lib/utils'

interface MessageItemProps {
  message: ChatMessage
}

export function MessageItem({ message }: MessageItemProps) {
  const isUser = message.role === 'user'

  return (
    <div className={cn('flex', isUser ? 'justify-end' : 'justify-start')}>      <div
        className={cn(
          'max-w-xs lg:max-w-md xl:max-w-lg rounded-lg p-4',
          isUser
            ? 'bg-blue-500 text-white rounded-br-none'
            : 'bg-gray-100 dark:bg-gray-800 rounded-bl-none border border-gray-200 dark:border-gray-700'
        )}
      >
        <div className="text-sm whitespace-pre-wrap">{message.content}</div>

        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
            <div className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-2">
              Sources ({message.sources.length}):
            </div>
            <div className="space-y-1">
              {message.sources.slice(0, 3).map((source, index) => (
                <CitationWidget key={index} source={source} />
              ))}
              {message.sources.length > 3 && (
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  +{message.sources.length - 3} more sources
                </div>
              )}
            </div>
          </div>
        )}

        {message.metrics && (
          <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
            <EvaluationWidget metrics={message.metrics} />
          </div>
        )}

        <div className="text-xs opacity-70 mt-2">
          {message.timestamp.toLocaleTimeString()}
        </div>
      </div>
    </div>
  )
}