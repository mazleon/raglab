"use client"

import { useQuery } from '@tanstack/react-query'
import type { Experiment } from '@/types'

interface ExperimentsResponse {
  experiments: Experiment[]
  count: number
}

async function fetchExperiments(): Promise<Experiment[]> {
  const response = await fetch('/api/experiments')
  if (!response.ok) {
    throw new Error('Failed to fetch experiments')
  }
  const data = (await response.json()) as ExperimentsResponse
  return data.experiments ?? []
}

export function useExperiments() {
  return useQuery({
    queryKey: ['experiments'],
    queryFn: fetchExperiments,
    staleTime: 1000 * 60 * 5,
  })
}
