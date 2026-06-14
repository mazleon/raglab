# RAGLab

**A modular, research-grade platform for benchmarking RAG architectures,
embeddings, rerankers, retrievers, and LLMs under identical conditions.**

RAGLab runs the same query across many retrieval architectures and compares
retrieval quality, faithfulness, latency, token usage, and cost — so you make
apples-to-apples decisions instead of guessing. Every component (embedder,
vector store, retriever, reranker, LLM, architecture, evaluator, tracer) is
swappable via YAML with **no code changes**.

- **Runs fully offline with zero API keys** — hashing embedder + in-memory
  Qdrant + BM25 + an extractive LLM — and scales up to OpenAI / OpenRouter /
  Gemini / Cohere, RAGAS, and LangFuse/LangSmith by editing config + setting keys.
- **13 RAG architectures** implemented behind one `Pipeline` interface.
- **Production-grade error handling**: fatal mistakes (bad model/key) fail fast
  with a clear message; transient errors (rate limits, 5xx) retry with backoff;
  a failing benchmark cell or judge is recorded and skipped, never aborting the run.

## Quickstart (offline, no keys, no Docker)

```bash
uv venv && uv pip install -e ".[dev]"

# One-shot query (ingests the sample corpus into an in-memory store, then asks):
raglab query "How does Reciprocal Rank Fusion score documents?" \
  --config configs/pipelines/agentic.yaml --ingest examples/docs

# Benchmark a matrix and produce a leaderboard + SQLite experiment store:
raglab bench --config configs/benchmarks/offline.yaml
# -> reports/leaderboard-latest.{csv,html}, reports/experiments.db

# Inspect what's registered:
raglab architectures      # 13 architectures
raglab components         # embedders / retrievers / rerankers / llms / ...
```

## Architectures (13)

`naive`, `hybrid` (BM25 + dense + RRF/MMR + rerank), `agentic` (LangGraph
self-correcting loop), `advanced`, `crag`, `self_rag`, `adaptive`, `multi_hop`,
`reflective`, `deep_search`, `hierarchical`, `graph_rag` (networkx / optional
Neo4j), `kg_vector_rag`. Each is a distinct control flow on the shared
interfaces — see `src/raglab/pipelines/`.

## Configuration (modular)

```
configs/
  ingest.yaml                # ingestion (default for `raglab ingest`)
  pipelines/                 # single-query pipelines (`raglab query -c ...`)
    naive.yaml  hybrid.yaml  agentic.yaml  cloud.yaml
  benchmarks/                # benchmark matrices (`raglab bench -c ...`)
    offline.yaml             # no keys (default for `raglab bench`)
    openai.yaml  openrouter.yaml  gemini.yaml  ragas.yaml
  README.md                  # provider/model matrix + persistence guide
```

See [`configs/README.md`](configs/README.md) for the full provider/model matrix.

## Providers

| Role        | Providers (config name)                                        | Notes |
|-------------|----------------------------------------------------------------|-------|
| Embeddings  | `hashing` (offline), `openai`, `cohere`, `gemini`, `bge_local`, `e5_local` | OpenRouter is chat-only |
| Rerankers   | `noop` (offline), `cohere`, `cross_encoder` (local)            | Cohere `rerank-v4.0-fast` / `rerank-v3.5` |
| LLMs        | `echo` (offline), `openai`, `openrouter`, `gemini`            | OpenRouter: prefer `deepseek/deepseek-chat`; `:free` slugs are rate-limited |

Set keys in `.env` (copy `.env.example`). RAGLab loads it automatically and
reconciles `LANGFUSE_BASE_URL`→`LANGFUSE_HOST` and `LANGSMITH_API_KEY`→
`LANGCHAIN_API_KEY`.

```bash
uv pip install -e ".[providers,local,eval,obs,parsers]"   # install only what you need
```

| Extra        | Unlocks                                                       |
|--------------|--------------------------------------------------------------|
| `providers`  | OpenAI / Cohere / Gemini embeddings, Cohere Rerank, OpenAI / OpenRouter / Gemini chat |
| `local`      | BGE/E5 embeddings + local cross-encoder reranker             |
| `neo4j`      | Neo4j backend for GraphRAG (networkx is the in-core default) |
| `eval`       | RAGAS metrics                                                |
| `obs`        | LangFuse tracing                                             |
| `parsers`    | PDF + DOCX ingestion                                         |

### Full cloud stack (verified)

`configs/pipelines/cloud.yaml` runs Gemini embeddings + Cohere Rerank +
OpenRouter (DeepSeek) through the agentic loop with LangFuse/LangSmith tracing:

```bash
raglab query "How does RRF work and what reranker options exist?" \
  --config configs/pipelines/cloud.yaml --ingest examples/docs
```

## Evaluation

- **Built-in proxy metrics** (offline, no LLM): `context_recall_proxy`,
  `answer_relevancy_proxy`, `answer_nonempty`, `faithfulness_proxy`.
- **LLM-as-judge**: `faithfulness`, `answer_quality`, `grounding`, `citation`,
  `reasoning` — the judge model is any configured provider. Judge spend is
  reported separately as `judge_cost_usd` / `judge_tokens`.
- **RAGAS**: `faithfulness`, `answer_relevancy`, `context_precision`,
  `context_recall` (needs `[eval]` + a judge LLM).

A judge or RAGAS failure is captured in the leaderboard `error` column and
skipped — the rest of the matrix still completes.

```bash
raglab bench --config configs/benchmarks/openrouter.yaml   # LLM-judged, real keys
```

## API

```bash
uvicorn raglab.api:app --reload
```

| Method | Path | Body / Response |
|--------|------|-----------------|
| GET | `/health` | `{ "status": "ok" }` |
| GET | `/architectures` | List registered architectures |
| POST | `/query` | `{query, config, ingest_path?}` |
| POST | `/benchmark` | `{config}` |
| GET | `/experiments` | Recorded benchmark experiments (SQLite) |
| GET | `/dashboard` | HTML experiment dashboard |

Provider/config errors map to clean HTTP codes (400 for config, 502 for upstream
provider failures) rather than stack traces.

## Persistent vector store

Configs default to in-memory Qdrant. For persistence either run the Docker
server and set `QDRANT_URL`, or use embedded on-disk mode:

```bash
docker compose -f docker/docker-compose.yml up -d   # Qdrant on :6333
export QDRANT_URL=http://localhost:6333
# ...or set `vectorstore.location: qdrant_storage` in the config (no server).
```

An explicit `location:` in a config always wins over the ambient `QDRANT_URL`,
so a config that asks for `:memory:` is never silently redirected to a server.

## Testing & quality

```bash
pytest                 # unit + integration (in-memory Qdrant, no keys)
ruff check src tests
mypy src
```

CI (`.github/workflows/ci.yml`): ruff + mypy + unit on PR; integration on main.

## Architecture & roadmap

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for system / sequence /
data-flow diagrams and component contracts, and [docs/ROADMAP.md](docs/ROADMAP.md)
for the (now-implemented) Phases 2–6 and remaining items.
