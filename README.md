# RAGLab

**A modular, research-grade platform for benchmarking RAG architectures,
embeddings, rerankers, retrievers, and LLMs under identical conditions.**

RAGLab runs the same query across multiple retrieval architectures and compares
retrieval quality, faithfulness, latency, token usage, and cost — so you can
make apples-to-apples decisions instead of guessing. Every component
(embedder, vector store, retriever, reranker, LLM, architecture, evaluator,
tracer) is swappable via YAML with **no code changes**.

> **Milestone 1** ships a working vertical slice on a genuinely modular core.
> It runs **fully offline with zero API keys** (hashing embedder + in-memory
> Qdrant + BM25 + an extractive LLM), and scales up to OpenAI / Cohere /
> OpenRouter, RAGAS, and LangFuse/LangSmith by editing config + setting keys.

## Quickstart (offline, no keys, no Docker)

```bash
uv venv && uv pip install -e ".[dev]"

# One-shot query (ingests the sample corpus into an in-memory store, then asks):
raglab query "How does Reciprocal Rank Fusion score documents?" \
  --config configs/agentic.yaml --ingest examples/docs

# Benchmark a matrix and produce a leaderboard:
raglab bench --config configs/benchmark.yaml
# -> reports/leaderboard-latest.{csv,html}

# Inspect what's registered:
raglab architectures
raglab components
```

## With a persistent vector store + cloud providers

```bash
docker compose -f docker/docker-compose.yml up -d   # Qdrant on :6333
cp .env.example .env                                # add OPENAI/COHERE/OPENROUTER keys
export QDRANT_URL=http://localhost:6333

raglab ingest examples/docs --config configs/ingest.yaml
raglab query  "..."         --config configs/hybrid.yaml
```

Install extras as needed:

| Extra        | Unlocks                                           |
|--------------|---------------------------------------------------|
| `providers`  | OpenAI / Cohere / Gemini embeddings, Cohere Rerank, OpenAI & OpenRouter chat |
| `local`      | BGE/E5 embeddings + local cross-encoder reranker  |
| `neo4j`      | Neo4j backend for GraphRAG                        |
| `eval`       | RAGAS metrics                                     |
| `obs`        | LangFuse tracing                                  |
| `parsers`    | PDF + DOCX ingestion                              |

```bash
uv pip install -e ".[providers,local,eval,obs,parsers]"
```

## API

```bash
uvicorn raglab.api:app --reload
```

Endpoints:

| Method | Path | Body / Response |
|--------|------|-----------------|
| GET | `/health` | `{ "status": "ok" }` |
| GET | `/architectures` | List registered architectures |
| POST | `/query` | `{query, config, ingest_path?}` |
| POST | `/benchmark` | `{config}` |
| GET | `/experiments` | List recorded benchmark experiments |
| GET | `/dashboard` | HTML experiment dashboard |

Example:

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How does RRF work?", "config": "configs/hybrid.yaml", "ingest_path": "examples/docs"}'
```

## Testing

```bash
# Unit tests (no external services)
pytest tests/unit

# Integration tests (in-memory Qdrant by default)
pytest tests/integration

# Lint + type check
ruff check src tests
mypy src
```

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for system / sequence / data-flow
diagrams and [docs/ROADMAP.md](docs/ROADMAP.md) for what lands in Phases 2–6
(GraphRAG/Neo4j, the remaining architectures, more providers, an experiment
dashboard, compressed retrieval, CI/CD).

Implemented architectures: **Naive RAG**, **Hybrid RAG** (BM25 + dense + RRF/MMR
+ rerank), **Agentic RAG** (LangGraph self-correcting loop). The `Pipeline`
registry also supports stubs for future architectures, so adding a new one only
requires implementing `run()` — no wiring changes.
