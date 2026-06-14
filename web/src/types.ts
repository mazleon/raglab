export interface RAGResult {
  answer: string
  context_texts: string[]
  metrics: {
    latency_ms: number
    total_tokens: number
    usd_cost: number
    retriever_hits?: number
  }
  architecture: string
  model: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  sources?: string[]
  metrics?: any
  isError?: boolean
}

export interface Experiment {
  id: string
  name: string
  architecture: string
  embedding: string
  retrieval: string
  reranker: string
  metrics: Record<string, number>
  timestamp: string
}