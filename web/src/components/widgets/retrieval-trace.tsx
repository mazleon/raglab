"use client"

interface RetrievalTraceWidgetProps {
  trace?: any
}

export function RetrievalTraceWidget({ trace }: RetrievalTraceWidgetProps) {
  if (!trace) return null

  return (
    <div className="bg-gray-50 dark:bg-gray-700/30 rounded p-3 border border-gray-200 dark:border-gray-700">
      <div className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">
        Retrieval Trace
      </div>
      <div className="space-y-1 text-xs">
        <div className="flex justify-between">
          <span className="text-gray-600 dark:text-gray-400">Architecture:</span>
          <span className="font-medium">{trace.architecture || 'N/A'}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600 dark:text-gray-400">Embedding:</span>
          <span className="font-medium">{trace.embedding || 'N/A'}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600 dark:text-gray-400">Retriever:</span>
          <span className="font-medium">{trace.retrieval || 'N/A'}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600 dark:text-gray-400">Reranker:</span>
          <span className="font-medium">{trace.reranker || 'N/A'}</span>
        </div>
      </div>
    </div>
  )
}