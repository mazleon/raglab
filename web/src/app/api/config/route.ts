import { NextResponse } from 'next/server'
import { backend } from '@/lib/backend'

// Offline fallback so the UI still renders if the backend is unreachable.
const FALLBACK = {
  models: [{ id: 'echo', name: 'Echo (Offline)', provider: 'echo', description: 'Extractive QA', available: true }],
  embeddings: [{ id: 'hashing', name: 'Hashing (Offline)', provider: 'hashing', dimensions: 384, description: 'Local hashing', available: true }],
  pipelines: [
    { id: 'naive', name: 'Naive RAG', description: 'Dense retrieval → generate' },
    { id: 'hybrid', name: 'Hybrid RAG', description: 'Dense + BM25 → generate' },
    { id: 'agentic', name: 'Agentic RAG', description: 'Self-correcting loop' },
  ],
  architectures: ['naive_rag', 'hybrid_rag', 'agentic_rag'],
  default_model: 'echo',
  default_embedding: 'hashing',
  default_pipeline: 'naive',
}

export async function GET() {
  try {
    const res = await fetch(backend('/config/providers'), { cache: 'no-store' })
    if (!res.ok) return NextResponse.json(FALLBACK)
    const data = await res.json()
    return NextResponse.json({
      models: data.models ?? FALLBACK.models,
      embeddings: (data.embeddings ?? []).map((e: Record<string, unknown>) => ({
        ...e,
        dimensions: e.dim ?? e.dimensions ?? 0,
      })),
      pipelines: data.pipelines ?? FALLBACK.pipelines,
      architectures: data.architectures ?? FALLBACK.architectures,
      providers: data.providers ?? {},
      default_model: data.defaults?.model ?? 'echo',
      default_embedding: data.defaults?.embedding ?? 'hashing',
      default_pipeline: data.defaults?.pipeline ?? 'naive',
    })
  } catch {
    return NextResponse.json(FALLBACK)
  }
}
