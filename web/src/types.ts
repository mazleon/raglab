export interface RAGContext {
  score: number
  source: string
  text: string
}

export interface RAGMetrics {
  latency_ms: number
  total_tokens: number
  usd_cost: number
  retries?: number
  retriever_hits?: number
  // Runtime config annotations (not from backend)
  _pipeline?: string
  _model?: string
  _embedding?: string
}

export interface RAGResult {
  architecture: string
  answer: string
  contexts: RAGContext[]
  metrics: RAGMetrics
  trajectory: string[]
}

export interface TrajectoryStep {
  name: string
  detail?: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  sources?: RAGContext[]
  metrics?: RAGMetrics
  trajectory?: TrajectoryStep[]
  isStreaming?: boolean
  isError?: boolean
}

/* ── Auth / Sessions ── */
export interface User {
  id: string
  email: string
  name: string
  tenant_id: string
  role: string
}

export interface Conversation {
  id: string
  title: string
  pipeline: string
  created_at: string
  updated_at: string
}

export interface StoredMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  metadata?: {
    sources?: RAGContext[]
    metrics?: RAGMetrics
    architecture?: string
  }
  created_at: string
}

export interface Experiment {
  experiment_id: string
  architecture: string
  embedding: string
  retrieval: string
  reranker: string
  llm: string
  n_questions: number
  avg_latency_ms: number
  total_cost_usd: number
  avg_tokens: number
  timestamp: string
  context_recall_proxy: number
  answer_relevancy_proxy: number
  answer_nonempty: number
  judge_faithfulness?: number
  judge_answer_quality?: number
  answer_cost_usd?: number
  judge_cost_usd?: number
  judge_tokens?: number
  error?: string
}

/* ── Document / Knowledge ── */
export interface Document {
  id: string
  name: string
  type: string
  size: number
  status: 'pending' | 'indexing' | 'indexed' | 'failed'
  uploaded_at: string
  chunks?: number
  error?: string
}

/* ── Configuration Options ── */
export interface ModelOption {
  id: string
  name: string
  provider: string
  description: string
  available: boolean
}

export interface EmbeddingOption {
  id: string
  name: string
  provider: string
  dimensions: number
  description: string
  available: boolean
}

export interface PipelineOption {
  id: string
  name: string
  description: string
}

export interface RAGConfig {
  pipeline: string
  model: string
  embedding: string
  ingest_path?: string
}
