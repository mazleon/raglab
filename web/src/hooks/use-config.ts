"use client"

import { useQuery } from '@tanstack/react-query'
import type { ModelOption, EmbeddingOption, PipelineOption } from '@/types'
import { apiGet } from '@/lib/api'

export interface ConfigData {
  models: ModelOption[]
  embeddings: EmbeddingOption[]
  pipelines: PipelineOption[]
  architectures: string[]
  default_model: string
  default_embedding: string
  default_pipeline: string
}

export function useConfig() {
  return useQuery({
    queryKey: ['config'],
    queryFn: () => apiGet<ConfigData>('/api/config'),
    staleTime: 1000 * 60 * 10, // 10 minutes — config rarely changes
  })
}