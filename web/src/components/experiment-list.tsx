"use client"

import { Experiment } from '@/types'

interface ExperimentListProps {
  experiments: Experiment[]
}

export function ExperimentList({ experiments }: ExperimentListProps) {
  if (experiments.length === 0) {
    return (
      <div className="text-center py-12 bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-gray-200 dark:border-gray-700">
        <div className="text-gray-500 dark:text-gray-400">No experiments found</div>
        <div className="text-sm text-gray-400 dark:text-gray-500 mt-1">
          Run a benchmark to get started
        </div>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {experiments.map((experiment) => (
        <ExperimentCard key={experiment.id} experiment={experiment} />
      ))}
    </div>
  )
}

function ExperimentCard({ experiment }: { experiment: Experiment }) {
  const getMetricColor = (value: number, type: 'good' | 'neutral' | 'bad') => {
    if (type === 'good') return 'text-green-600 dark:text-green-400'
    if (type === 'bad') return 'text-red-600 dark:text-red-400'
    return 'text-gray-600 dark:text-gray-400'
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 hover:shadow-lg transition-shadow cursor-pointer">
      <div className="flex justify-between items-start mb-3">
        <div>
          <h3 className="font-medium text-gray-900 dark:text-gray-100 truncate">
            {experiment.name}
          </h3>
          <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            {experiment.architecture} • {experiment.embedding}
          </div>
        </div>
        <div className="text-xs text-gray-500 dark:text-gray-400">
          {new Date(experiment.timestamp).toLocaleDateString()}
        </div>
      </div>

      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-gray-600 dark:text-gray-400">Recall:</span>
          <span className={getMetricColor(experiment.metrics.context_recall_proxy || 0, 'good')}>{(experiment.metrics.context_recall_proxy * 100).toFixed(1)}%</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-600 dark:text-gray-400">Relevancy:</span>
          <span className={getMetricColor(experiment.metrics.answer_relevancy_proxy || 0, 'good')}>{(experiment.metrics.answer_relevancy_proxy * 100).toFixed(1)}%</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-600 dark:text-gray-400">Latency:</span>
          <span className="text-gray-900 dark:text-gray-100">{experiment.metrics.avg_latency_ms.toFixed(0)}ms</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-600 dark:text-gray-400">Cost:</span>
          <span className="text-gray-900 dark:text-gray-100">${experiment.metrics.total_cost_usd.toFixed(4)}</span>
        </div>
      </div>
    </div>
  )
}