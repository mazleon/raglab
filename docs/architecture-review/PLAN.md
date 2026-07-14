# RAGLab Architecture Review — Unified Improvement & Restructuring Plan

**Verdict (all three reviews agree):** The architecture is fundamentally sound. The registry/interfaces/config core is genuinely strong — no business code imports concrete providers; components swap via YAML. **This is consistency cleanup and dead-code removal, not a rewrite.** A big-bang folder restructure is explicitly *not* warranted (both backend and agentics reviews recommend against merging retrievers/rerankers/vectorstores into a `retrieval/` package).

Detailed evidence: `docs/architecture-review/{backend,frontend,agentics}.md`.

---

## Cross-cutting P0 — do now (tiny diffs, zero behavior change, low risk)

These are mechanical wins flagged independently by two or more reviews.

| # | Change | Files | Risk |
|---|---|---|---|
| P0.1 | Delete dead `pipelines/stubs.py` + its import in `pipelines/__init__.py` | 2 | none — empty `_PLANNED={}`, registers nothing |
| P0.2 | `rm backend.log nohup.out` (already gitignored) | working tree | none |
| P0.3 | Extract `core/text.py` (`content_tokens` + shared `_TOKEN`/`_STOP`); reuse from `agents/grading.py` + `evaluation/builtin.py`; delete copies | new + 2 | low — near-identical token/stopword sets |
| P0.4 | Extract `core/utils.py::deep_merge`; reuse from `core/overrides.py` + `benchmarks/runner.py`; delete copies | new + 2 | low |
| P0.5 | Rename `_content_tokens` → `content_tokens` (private name used across 5 modules) | `agents/grading.py` + 4 importers | trivial |
| P0.6 | Drop dead `llm` param from `reasoning.classify_complexity` + `reasoning.decompose`; update callers | 3 | none — param unused |
| P0.7 | `Neo4jGraphStore.communities()` → `raise NotImplementedError` (currently silently returns `[]`) | 1 | none — no caller |
| P0.8 | Align `GraphStore` Protocol with real entry point (`build_from_chunks`) | `graph/__init__.py` + 2 impls | low |
| P0.9 | Route `routers/query.py` through `server.sessions` (cached, tenant-pinned) like `chat.py` | `routers/query.py` | low-medium — `/query` gains tenant pinning; add `test_routers_query.py` first |
| P0.10 | **Frontend:** delete empty `web/src/stores/` + remove `zustand` dep | `package.json` + dir | none — zero imports |
| P0.11 | **Frontend:** `import 'server-only'` in `lib/backend.ts` | 1 line | none |
| P0.12 | **Frontend:** fix 3 theme leaks — drop `bg-slate-900` on `<option>` (model-selector, knowledge page); replace `dark:` variants in `experiments/page.tsx` with tokens | 3 files | visual-only |
| P0.13 | **Frontend:** delete unused `useConversation` hook (or wire it into `chat/page.tsx` — recommend delete) | 1-2 | low |

## P1 — structural, one PR each (needs sign-off)

| # | Change | Files | Risk |
|---|---|---|---|
| P1.1 | Move `errors.py` → `core/errors.py` (keep one-line re-export shim to avoid touching ~20 importers at once) | core + shim | low (wide but mechanical) |
| P1.2 | Move `ingestion/store.py` → `accounts/documents.py` (it's per-tenant user-owned state; CLI ingest doesn't use it) | `routers/documents.py` + move | low |
| P1.3 | Rename `agents/` → `reasoning/` (it's shared heuristics, not the agent runtime which lives in `pipelines/agentic.py`); add compat shim | 9 pipeline importers + shim | medium |
| P1.4 | Rename LLM files for symmetry with embeddings/rerankers: `openai_compat.py` → `openai_llm.py` + `openrouter_llm.py`, `echo.py` → `echo_llm.py` | `llms/__init__.py` + files | none — registry names unchanged |
| P1.5 | Collapse the three `generate` wrappers → one (`helpers.generate` + `generate_with_instruction`; `BasePipeline._generate` delegates; `AgenticRAG._generate` → `_generate_node`) | base/helpers/agentic + verify Phase-3 | medium |
| P1.6 | Register evaluators (`@register("evaluator", …)`) + `build_evaluator(cfg)`; benchmark runner uses `registry.create`; wrap `evaluate_builtin` in a class. Completes the swappable-component story. | eval + config + runner | medium |
| P1.7 | Add `cleaner` component kind (Protocol + `@register("cleaner","default")` + `build_cleaner`); `IngestionPipeline` gets it from config instead of hardcoding `clean_documents` | interfaces + config + cleaners + pipeline | low |
| P1.8 | Rename `experiments/store.py` → `catalog.py` (disambiguate from 4 other "store" modules) | 2 importers | low |
| P1.9 | **Frontend:** route groups `(auth)` / `(app)` with layouts; delete `BARE_ROUTES` pathname hack in `app-shell.tsx` | moves + 2 layouts | medium (URLs unchanged) |
| P1.10 | **Frontend:** `lib/api.ts` client wrapper; route all hook `fetch` through it; normalize `ApiError` | new + 6 hooks | low-medium |
| P1.11 | **Frontend:** add `loading.tsx` / `error.tsx` / `not-found.tsx`; remove inline spinners | 3 new + simplify pages | low |

## P2 — defer until concrete need

- `components/ui/` primitive set (only when a 4th/5th form page appears)
- OpenAPI codegen from FastAPI, or **zod parsing of SSE events in `use-chat-stream.ts`** (highest-value P2 — kills silent backend-frontend drift)
- `retrieval/` superpackage (not justified at current size)
- Split `pipelines/` into `rag/`+`eval/` only if it grows past ~25 files
- Refactor `build_retriever` ladder only if a 6th retriever is added
- Remove unused `WorkflowMemory` / `GraphMemory` (or wire a consumer)
- `types.ts` split into `lib/types/{chat,auth,config,document}.ts` when it crosses ~200 lines

## Folder/naming target (post P0+P1) — minimal, industry-standard

```
src/raglab/
  core/           interfaces (+GraphStore, +Cleaner), types, registry, config (+build_cleaner, +build_evaluator),
                  overrides, errors (moved), text (new), utils (new)
  reasoning/       renamed from agents/ — grading, critic, rewrite, reasoning
  pipelines/      base, helpers, naive…graph_rag (stubs.py deleted)
  retrieval       (NOT created — keep retrievers/, rerankers/, vectorstores/, embeddings/ flat)
  memory/          unchanged (coherent)
  graph/           impls stay; Protocol moves to core/
  evaluation/      @register evaluators (P1)
  benchmarks/      experiments/ ingestion/ accounts/ (+documents.py) server/ routers/
  llms/            openai_llm, openrouter_llm, gemini_llm, echo_llm, metered, costs
```

```
web/src/
  app/  (auth)/{login,register}/layout  (app)/{chat,agents,knowledge,memory,experiments,evaluations} + loading/error/not-found
  components/  app-shell, theme-toggle, …  (ui/ deferred)
  hooks/  lib/  {backend (+server-only), api (new), provider-colors (new), utils}
  (stores/ deleted)
```

## What is already good — DO NOT touch
- `core/registry.py` + `@register` discipline + `core/interfaces.py` Protocols + `core/config.py` composition root
- `core/types.py` dataclasses (Chunk/Document/ScoredChunk/RAGResult/RunMetrics/TrajectoryStep)
- `BasePipeline` strategy pattern across 13 architectures
- `MemoryManager`/`BaseMemoryStore`/`MemoryScope` layering; SQLite-source-of-truth + Qdrant-derived
- BFF pattern in `web/` (browser → `app/api/*` → FastAPI via `lib/backend.ts`); isolated SSE in `use-chat-stream.ts`; TanStack Query discipline; theme token system
- Lazy-import + `MissingDependencyError` + offline vertical slice (zero API keys)

## Test guardrails before P0.9 / P1.2
- Add `tests/unit/test_routers_query.py` before P0.9 (`/query` + `/benchmark` currently untested)
- Add `tests/unit/test_accounts_documents.py` (post P1.2) — document catalog currently untested