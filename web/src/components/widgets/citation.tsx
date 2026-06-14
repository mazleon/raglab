"use client"

interface CitationWidgetProps {
  source: string
  index?: number
}

export function CitationWidget({ source, index }: CitationWidgetProps) {
  return (
    <div className="text-xs bg-gray-50 dark:bg-gray-700/50 rounded p-2 border-l-4 border-blue-500">
      <div className="font-medium text-gray-700 dark:text-gray-300">
        Source {index !== undefined ? index + 1 : ''}
      </div>
      <div className="text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">
        {source}
      </div>
    </div>
  )
}