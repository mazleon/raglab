"use client"

import { useQuery } from '@tanstack/react-query'
import type { ModelOption, EmbeddingOption, PipelineOption } from '@/types'

export interface ConfigData {
  models: ModelOption[]
  embeddings: EmbeddingOption[]
  pipelines: PipelineOption[]
  architectures: string[]
  default_model: string
  default_embedding: string
  default_pipeline: string
}

async function fetchConfig(): Promise<ConfigData> {
  const res = await fetch('/api/config')
  if (!res.ok) throw new Error('Failed to fetch configuration')
  return res.json()
}

export function useConfig() {
  return useQuery({
    queryKey: ['config'],
    queryFn: fetchConfig,
    staleTime: 1000 * 60 * 10, // 10 minutes — config rarely changes
  })
}
