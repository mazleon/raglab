# RAGLab configs

Experiment configs are plain YAML resolved into wired components by the registry
(`src/raglab/core/config.py`). Swapping any component — embedder, retriever,
reranker, LLM, architecture — is a YAML edit; no code changes.

## Layout

```
configs/
  ingest.yaml              # ingestion (CLI default for `raglab ingest`)
  pipelines/               # single-query pipelines (CLI `raglab query -c ...`)
    naive.yaml   hybrid.yaml   agentic.yaml   cloud.yaml
  benchmarks/              # benchmark matrices (CLI `raglab bench -c ...`)
    offline.yaml           # no keys (CLI default for `raglab bench`)
    openai.yaml            # LLM-as-judge via OpenAI
    openrouter.yaml        # LLM-as-judge via OpenRouter
    gemini.yaml            # LLM-as-judge via Gemini (free-tier delay)
    ragas.yaml             # RAGAS metrics via OpenAI
```

## Providers & models

| Section          | Provider     | Example model id                | Needs                         |
|------------------|--------------|---------------------------------|-------------------------------|
| `embedding.name` | `hashing`    | — (offline default)             | nothing                       |
|                  | `openai`     | `text-embedding-3-large`        | `[providers]` + OPENAI_API_KEY |
|                  | `cohere`     | `embed-english-v3.0`            | `[providers]` + COHERE_API_KEY |
|                  | `gemini`     | `gemini-embedding-001` (768d)   | `[providers]` + GOOGLE_API_KEY |
|                  | `bge_local`/`e5_local` | `BAAI/bge-small-en-v1.5` | `[local]` (no key)           |
| `reranker.name`  | `noop`       | —                               | nothing                       |
|                  | `cohere`     | `rerank-v4.0-fast`, `rerank-v3.5` | `[providers]` + COHERE_API_KEY |
|                  | `cross_encoder` | `cross-encoder/ms-marco-MiniLM-L-6-v2` | `[local]`           |
| `llm.provider`   | `echo`       | — (offline extractive)          | nothing                       |
|                  | `openai`     | `gpt-4o-mini`, `gpt-4o`         | `[providers]` + OPENAI_API_KEY |
|                  | `openrouter` | `deepseek/deepseek-chat`, `anthropic/claude-3.5-sonnet` | `[providers]` + OPENROUTER_API_KEY |
|                  | `gemini`     | `gemini-2.5-flash`, `gemini-2.5-pro` | `[providers]` + GOOGLE_API_KEY |

> OpenRouter is **chat-only** (no embeddings). `:free` slugs are heavily
> rate-limited and frequently require the paid slug — prefer
> `deepseek/deepseek-chat` (cheap + reliable) as a default.

## LLM-as-judge

Benchmark `evaluation` blocks can score answers with a judge LLM:

```yaml
evaluation:
  judges: [faithfulness, answer_quality]   # also: grounding, citation, reasoning
  judge_delay_s: 0                         # >0 to respect free-tier rate limits
  judge_llm: { provider: openrouter, model: deepseek/deepseek-chat, max_tokens: 256 }
```

Judge spend is reported separately as `judge_cost_usd` / `judge_tokens`. A judge
or RAGAS failure is recorded in the `error` column and skipped — it never aborts
the rest of the matrix.

## Persistent vector store

The configs default to in-memory Qdrant. For a store that survives across
processes, either:

* set an env var: `export QDRANT_URL=http://localhost:6333` (Docker server), or
* point `vectorstore.location` at a folder for embedded on-disk Qdrant:

```yaml
vectorstore: { name: qdrant, location: qdrant_storage, distance: cosine }
```

Then `raglab ingest` once and run benchmarks with `corpus:` omitted to reuse the
pre-ingested collection.
```
