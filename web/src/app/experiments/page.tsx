"use client"

import { useQuery } from '@tanstack/react-query'
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
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          Experiments
        </h1>
        <button className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors">
          New Experiment
        </button>
      </div>

      <ExperimentList experiments={experiments} />
    </div>
  )
}