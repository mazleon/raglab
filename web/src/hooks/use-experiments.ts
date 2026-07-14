"use client"

import { useQuery } from '@tanstack/react-query'
import type { Experiment } from '@/types'
import { apiGet } from '@/lib/api'

interface ExperimentsResponse {
  experiments: Experiment[]
  count: number
}

async function fetchExperiments(): Promise<Experiment[]> {
  const data = await apiGet<ExperimentsResponse>('/api/experiments')
  return data.experiments ?? []
}

export function useExperiments() {
  return useQuery({
    queryKey: ['experiments'],
    queryFn: fetchExperiments,
    staleTime: 1000 * 60 * 5,
  })
}