"use client"

import { useQuery } from '@tanstack/react-query'

async function fetchExperiments(): Promise<Experiment[]> {
  const response = await fetch('/api/experiments')
  if (!response.ok) {
    throw new Error('Failed to fetch experiments')
  }
  return response.json()
}

export function useExperiments() {
  return useQuery({
    queryKey: ['experiments'],
    queryFn: fetchExperiments,
    staleTime: 1000 * 60 * 5, // 5 minutes
  })
}