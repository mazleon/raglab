# RAGLab Architecture

## Design principle

Everything is an interface (`src/raglab/core/interfaces.py`) with one or more
registered implementations. Business logic depends only on the protocols; the
config layer (`core/config.py`) resolves YAML into wired components via the
registry (`core/registry.py`). Swapping any component is a YAML edit.

## System overview

```mermaid
flowchart LR
  subgraph Ingestion
    A[Documents] --> P[Parser] --> CL[Cleaner] --> CH[Chunker]
    CH --> EN[Enrich] --> E1[Embedder] --> Q[(Qdrant)]
  end
  subgraph Query
    U[Query] --> RT[Retriever]
    RT -->|dense| E2[Embedder] --> Q
    RT -->|sparse| BM[BM25]
    RT --> RR[Reranker] --> G[LLM Generate] --> ANS[Answer + citations]
  end
  subgraph Cross-cutting
    TR[Tracer: LangFuse/LangSmith]
    EV[Evaluator: RAGAS + builtin proxies + LLM judges]
    BR[Benchmark Runner] --> LB[CSV + HTML leaderboard]
  end
  ANS --> EV
  ANS --> TR
```

## Component contracts

| Kind          | Protocol      | M1 implementations |
|---------------|---------------|--------------------|
| parser        | `Parser`      | text, html, csv, pdf, docx |
| chunker       | `Chunker`     | recursive, fixed, parent_child |
| embedder      | `Embedder`    | hashing (offline), openai, cohere, bge_local, e5_local |
| vectorstore   | `VectorStore` | qdrant (in-memory or server) |
| retriever     | `Retriever`   | dense, bm25, hybrid (RRF/MMR), multi_query |
| reranker      | `Reranker`    | noop, cross_encoder, cohere |
| llm           | `LLM`         | echo (offline), openai, openrouter |
| architecture  | `Pipeline`    | naive_rag, hybrid_rag, agentic_rag + 10 stubs |
| evaluator     | `Evaluator`   | builtin proxies, ragas, llm judges |
| tracer        | `Tracer`      | noop, langfuse, langsmith (env) |

## Query sequence (Hybrid RAG)

```mermaid
sequenceDiagram
  participant U as User
  participant H as HybridRAG
  participant R as HybridRetriever
  participant F as RRF/MMR
  participant K as Reranker
  participant L as LLM
  U->>H: run(query)
  H->>R: retrieve(query, k)
  R->>R: dense.search + bm25.search
  R->>F: fuse(dense, bm25)
  F-->>H: fused candidates
  H->>K: rerank(query, candidates, top_n)
  K-->>H: top contexts
  H->>L: generate(context + question)
  L-->>U: answer + RunMetrics
```

## Agentic RAG state machine (LangGraph)

```mermaid
stateDiagram-v2
  [*] --> plan
  plan --> retrieve
  retrieve --> grade
  grade --> generate: score >= threshold OR retries exhausted
  grade --> rewrite: score < threshold
  rewrite --> retrieve
  generate --> critic
  critic --> generate: ungrounded (1 regeneration)
  critic --> cite: ok
  cite --> [*]
```

Defined in `src/raglab/pipelines/agentic.py`; nodes in `src/raglab/agents/`.

## Data flow types

`Document → Chunk → ScoredChunk → RAGResult` (`core/types.py`). `RAGResult`
carries the answer, scored contexts, an agent trajectory, and `RunMetrics`
(latency, prompt/completion tokens, USD cost, retriever hits, retries).

## Benchmark flow

`benchmarks/runner.py` expands the `matrix` cartesian product, gives each cell a
unique collection, ingests the corpus, runs the QA dataset, evaluates (builtin
proxies offline; RAGAS + LLM judges when configured), and writes a ranked
leaderboard.
