"use client"

interface EvaluationWidgetProps {
  metrics: any
}

export function EvaluationWidget({ metrics }: EvaluationWidgetProps) {
  const metricItems = [
    { key: 'latency_ms', label: 'Latency', format: (v: number) => `${v.toFixed(0)}ms` },
    { key: 'total_tokens', label: 'Tokens', format: (v: number) => v.toString() },
    { key: 'usd_cost', label: 'Cost', format: (v: number) => `$${v.toFixed(4)}` },
    { key: 'retriever_hits', label: 'Hits', format: (v: number) => v.toString() },
  ].filter(item => metrics && metrics[item.key] !== undefined)

  if (metricItems.length === 0) return null

  return (
    <div className="grid grid-cols-2 gap-2 text-xs">
      {metricItems.map((item) => (
        <div key={item.key} className="flex justify-between">
          <span className="text-gray-600 dark:text-gray-400">{item.label}:</span>
          <span className="font-medium text-gray-900 dark:text-gray-100">
            {item.format(metrics[item.key])}
          </span>
        </div>
      ))}
    </div>
  )
}