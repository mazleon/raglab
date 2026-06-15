"use client"

import { ExperimentList } from '@/components/experiment-list'
import { useExperiments } from '@/hooks/use-experiments'

export default function ExperimentsPage() {
  const { data: experiments = [], isLoading, error } = useExperiments()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 dark:text-red-400">Error loading experiments</div>
        <div className="text-sm text-gray-500 dark:text-gray-400 mt-2">
          {(error as Error).message}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gradient-cyan">
          Experiments
        </h1>
        <button className="px-5 py-2.5 bg-gradient-to-r from-cyan-500 to-violet-600 text-white rounded-xl font-medium text-sm btn-glow-cyan active:scale-95">
          New Experiment
        </button>
      </div>

      <ExperimentList experiments={experiments} />
    </div>
  )
}
