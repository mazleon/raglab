# Backend Architecture Review — src/raglab

Scope: `src/raglab/` (114 Python files across 17 top-level domain packages) plus `tests/`, `configs/`, `pyproject.toml`. `web/` (Next.js) is out of scope. Every claim below is backed by a file path; where the codebase is already good, it says so.

## Current Structure (what's here, with file paths)

```
src/raglab/
  __init__.py            — version only
  api.py                 — FastAPI app: CORS, one domain-error handler, includes 7 routers
  cli.py                 — Typer CLI: ingest / query / bench / architectures / components
  service.py             — Engine dataclass + build_engine() (shared composition root)
  env.py                 — idempotent .env loader + SDK env-var aliasing
  errors.py              — RaglabError hierarchy + call_with_retries()
  core/                  — interfaces.py (Protocols), types.py (dataclasses),
                          registry.py (@register/create/bootstrap), config.py (Pydantic +
                          builders), overrides.py (client override allow-list)
  accounts/              — auth.py (JWT + bcrypt), conversations.py, db.py (SQLite schema)
  server/                — sessions.py (engine cache + tenant config), streaming.py (SSE),
                          deps.py (current_user), state.py (MemoryManager singleton)
  routers/               — auth.py, chat.py, conversations.py, documents.py, config.py,
                          query.py, memory.py (FastAPI APIRouters)
  pipelines/             — base.py (BasePipeline + prompt helpers), helpers.py (shared
                          retrieve/rerank/generate/expand/dedup), stubs.py, + 13 arch modules
  retrievers/            — bm25, dense, hybrid, compressed, multi_query, fusion
  rerankers/             — cohere_rerank, cross_encoder, noop
  embeddings/            — openai_embed, cohere_embed, gemini_embed, local_embed, hashing
  llms/                  — openai_compat (OpenAI+OpenRouter), gemini_llm, echo, metered, costs
  vectorstores/          — qdrant_store
  ingestion/             — pipeline.py, store.py (doc catalog), enrich.py,
                          chunkers/{recursive,semantic}, cleaners/, parsers/{pdf,text}
  memory/                — manager.py, stores.py (10 types), base.py (BaseMemoryStore),
                          interfaces.py (MemoryStore Protocol), types.py, formation.py,
                          scoring.py, lifecycle.py, backends/{sqlite_store,vector_index}
  graph/                 — store.py (networkx), neo4j_store.py, extract.py
  agents/                — reasoning, critic, rewrite, grading (used by agentic pipeline)
  benchmarks/            — runner.py
  evaluation/            — ragas_eval, llm_judges, builtin, reports
  experiments/           — store.py (SQLite experiment catalog)
  observability/         — tracer.py (Langfuse/Langsmith)
```

`tests/` has `unit/` (8 files, 748 lines total) and `integration/` (1 file, `test_end_to_end.py`).

## Dependency Direction & Layering (real import edges, any violations)

The intended layering is: `api/cli` → `routers/server` → `service` → `core` → domain packages (`pipelines`, `retrievers`, `embeddings`, `llms`, `vectorstores`, `ingestion`, `memory`, `graph`, `accounts`). The registry pattern means **no business code imports a concrete provider module** — it all goes through `registry.create(kind, name, ...)`. This is genuinely well executed (see `src/raglab/core/registry.py` docstring, lines 1-10).

Real import edges traced:

- `src/raglab/api.py` → `routers.*`, `accounts.db`, `env`, `errors`. Correct — assembly only.
- `src/raglab/cli.py` → `core.registry`, `core.config`, `errors`, `ingestion.pipeline`, `service`. Correct.
- `src/raglab/service.py` → `core.config`, `core.interfaces`, `core.types`, `ingestion.pipeline`, `observability.tracer`, `env`. Correct composition root.
- `src/raglab/routers/*.py` → `server.deps`, `server.sessions`, `server.streaming`, `server.state`, `accounts.*`, `ingestion.store`, `service`, `core.*`. **Routers import `server`** — see below.
- `src/raglab/server/sessions.py` → `core.config`, `core.overrides`, `service`, `env`. Correct.
- `src/raglab/server/streaming.py` → `accounts.auth`, `core.types`, `errors`, `server.sessions`, `server.state`, `memory` (lazy). Correct.
- `src/raglab/ingestion/store.py` → `accounts.db`. **Upward/leak** — see below.
- `src/raglab/core/registry.py:80` → `raglab.errors`. **Core imports a sibling top-level module** (errors.py lives at `raglab/` root, not in `core/`). Minor.

Violations and smells:

1. **`routers` → `server` is a layer inversion** (P1). The intended layering puts `server` below `routers`, but routers depend on `server.deps/sessions/streaming/state` for wiring they need (auth dep, engine cache, SSE generator, memory singleton). Evidence: `routers/chat.py:19-21`, `routers/documents.py:23-24`, `routers/conversations.py:12`, `routers/memory.py:10`, `routers/auth.py:21`. This is not circular — `server` does **not** import `routers` (verified: `grep -rn "from raglab.routers" src/raglab/server/` returns nothing). But "server" as a package name for "request-time wiring helpers that routers call" is mis-named; the routers are the HTTP server layer. The actual wiring helpers (`sessions.py`, `deps.py`, `streaming.py`, `state.py`) are a service/composition layer the routers sit on top of, not a layer below them.

2. **`ingestion/store.py:18` imports `accounts.db.db_path`** (P1). The ingestion document-catalog reaches into the accounts package to reuse the app's SQLite path. This couples ingestion (a domain package that should be accounts-agnostic) to the accounts subsystem. The CLI ingest path (`cli.py` → `IngestionPipeline`) does not use this store; only `routers/documents.py` does. Either the document catalog belongs under `accounts/` (it is per-tenant, keyed by `tenant_id`) or the db path helper belongs in `core/` / a shared persistence module.

3. **`core/registry.py:80` imports `raglab.errors`** (P2). `errors.py` sits at the `raglab/` root rather than in `core/`, so `core` reaches up one level to a sibling. `core/config.py:19` does the same. Not harmful (no cycle — `errors.py` imports nothing from `raglab`), but `errors.py` is conceptually a `core` concern and its placement at the package root is non-idiomatic.

4. **No circular dependencies found.** The bootstrap import of all implementation packages (`registry.py:24-37` `_IMPL_PACKAGES`) is flat and one-directional. The `@register` side-effect pattern is sound — importing a package registers its classes; nothing imports back.

5. **`routers/query.py:20` imports `service.build_engine` directly**, bypassing `server.sessions`' engine cache (`get_engine`). So the `/query` endpoint builds a fresh engine per request while `/chat/stream` reuses a cached one. Inconsistent engine lifecycle for the same logical action (run an architecture). P2.

## Naming & Convention Findings (concrete inconsistencies with paths)

Good and consistent:
- `snake_case` modules throughout; no CamelCase files.
- Pipeline classes are `XxxRAG` (e.g. `NaiveRAG`, `AgenticRAG`, `CorrectiveRAG`) — consistent across all 13 in `src/raglab/pipelines/`.
- Provider adapters follow `<provider>_<kind>.py` for embeddings/rerankers (`openai_embed.py`, `cohere_rerank.py`) but see inconsistency below for LLMs.
- Registry "kind" names are lowercase and stable: `embedder`, `vectorstore`, `retriever`, `reranker`, `llm`, `chunker`, `parser`, `architecture`, `memory`.

Inconsistencies:
1. **LLM adapter file naming breaks the `<provider>_<kind>` pattern** (P2). Embeddings use `openai_embed.py` / `cohere_embed.py` / `gemini_embed.py`; rerankers use `cohere_rerank.py`. But LLMs use `openai_compat.py` (a technical name, not a provider name), `gemini_llm.py`, `echo.py`. The registered names are `openai`, `openrouter`, `gemini`, `echo` (`llms/openai_compat.py:161,168`, `llms/gemini_llm.py`). So `openai_compat.py` houses two providers (OpenAI + OpenRouter) under a file named for a protocol detail. Rename to `openai_llm.py` + `openrouter_llm.py` (or keep one `openai_compat.py` but the asymmetry vs embeddings is unexplained).

2. **Three different "store" modules with overlapping semantics** (P2 — naming only, not a bug):
   - `src/raglab/vectorstores/qdrant_store.py` — vector store (registry kind `vectorstore`).
   - `src/raglab/ingestion/store.py` — SQLite document catalog (not registered; called as `ingestion.store`).
   - `src/raglab/experiments/store.py` — SQLite experiment catalog.
   - `src/raglab/graph/store.py` — NetworkX graph store (registered as `architecture`-adjacent, no registry kind).
   - `src/raglab/memory/stores.py` — the 10 registered memory types (registry kind `memory`).
   "store" is overloaded. `ingestion/store.py` is really a *document catalog*; `experiments/store.py` is an *experiment catalog*. Consider `ingestion/catalog.py` / `experiments/catalog.py` for clarity.

3. **`pipelines/stubs.py` is dead-but-kept** (P1). `_PLANNED: dict[str, tuple[str, str]] = {}` (line 18) is empty; the registration loop at lines 35-36 iterates over nothing. The module's docstring says it's "intentionally empty but kept so future planned architectures register the same way." This is scaffolding for later — YAGNI today. It imports `BasePipeline` and `register` for no runtime effect.

4. **Two parallel "base class" styles** (acceptable, but worth noting):
   - Swappable components use **`Protocol`** contracts in `core/interfaces.py` — implementations do **not** inherit a base class, they just `@register` and duck-type. Correct and idiomatic for plug-and-play. Verified: `retrievers/dense.py`, `embeddings/openai_embed.py`, `llms/openai_compat.py` — none inherit a base.
   - Pipelines use a **concrete base class** `BasePipeline` in `pipelines/base.py:36` that all 13 architectures inherit. This is fine — pipelines share real state (`self.c = components`) and a `_generate` helper; a Protocol would buy nothing here.
   - Memory uses **both**: `memory/interfaces.py` defines the `MemoryStore` Protocol *and* `memory/base.py` defines `BaseMemoryStore` (concrete, used by all 10 in `memory/stores.py`). Both are exercised — `BaseMemoryStore` implements the shared SQLite+vector plumbing, `MemoryStore` is the contract `MemoryManager` depends on. This dual style is consistent within memory and not a duplication problem.

5. **`raglab` vs `RAGLab` casing in docs/strings** is inconsistent but harmless. Code identifiers are uniformly `raglab`.

## Boundary & API Cleanliness

Strong:
- **The registry is a clean seam.** `core/registry.py` is the only place that knows the set of implementation packages (`_IMPL_PACKAGES`, lines 24-37). Business code (`pipelines`, `benchmarks/runner.py`, `server/sessions.py`) calls `registry.create(kind, name, **kwargs)` and never `from raglab.embeddings.openai_embed import OpenAIEmbedder`. This is the single best architectural property of the codebase.
- **`core/interfaces.py` centralizes all component Protocols** (Parser, Chunker, Embedder, VectorStore, Retriever, Reranker, LLM, Pipeline, Evaluator) in one 111-line file. There is exactly one contract per kind, not one per package.
- **`core/types.py` centralizes the data flow types** (`Chunk`, `Document`, `ScoredChunk`, `LLMResponse`, `RAGResult`, `RunMetrics`, `TrajectoryStep`). Plain dataclasses, no provider coupling.
- **`core/overrides.py` enforces an allow-list** (`_ALLOWED_SECTIONS`, lines 20-29) so untrusted client overrides can't reach into observability/vectorstore internals. Re-validation runs through the same composition root, so a bad override raises the same `ConfigError` a bad YAML would.

Leaks to fix:
1. **`ingestion/store.py` → `accounts.db`** (P1, noted above). The document catalog is per-tenant and reads the *accounts* DB path. Either move the catalog into `accounts/` (it belongs with conversations/messages as user-owned state) or extract a shared `db_path()` into `core/` / a persistence helper.
2. **`routers/query.py` duplicates `routers/chat.py`'s composition logic** (P2). `chat.py` goes through `server.sessions.build_session_config` + `get_engine` (cached, tenant-pinned). `query.py` calls `core.config.load_config` + `core.overrides.apply_overrides` + `service.build_engine` directly, with no tenant pinning and no cache. Same logical action, two wiring paths. The `/query` endpoint should route through `server.sessions` too, or document why it intentionally doesn't (e.g. it's a CLI-mirror for ad-hoc runs).
3. **`server/state.py` lazy-imports `memory` inside `get_memory()`** (line 17) — fine, but the module-level `_memory` global plus a function-local import is an inconsistency with `server/sessions.py`, which imports `service` at module top. Minor style drift.
4. **No formal `__all__` outside `accounts/__init__.py` and `memory/__init__.py`.** Other `__init__.py` files only do side-effect imports for registration. This is intentional (registration is the point), so not a defect — but it means `from raglab.pipelines import X` has no documented public surface. Acceptable given the registry is the intended API.

## Config / DI / Component Wiring

This is the strongest part of the codebase.

- **Config**: `pyproject.toml` declares deps + a light default install that runs the full vertical slice offline (hashing embedder + in-memory Qdrant + BM25 + Echo extractive LLM). Paid providers behind extras (`providers`, `neo4j`, `local`, `eval`, `obs`, `parsers`). `configs/` holds YAML: `ingest.yaml`, `pipelines/{naive,hybrid,agentic,cloud}.yaml`, `benchmarks/`. `core/config.py` parses YAML → `ExperimentConfig` (Pydantic) → `build_components()` → `build_pipeline_from_components()`. Swapping any component is a YAML edit. Clean.
- **DI**: the registry (`@register` decorator + `create`/`bootstrap`) is the DI mechanism. Implementation modules lazy-import heavy/optional libs *inside* `__init__`/methods (e.g. `embeddings/openai_embed.py:29` `from openai import OpenAI` inside `_ensure()`), so importing the package never requires the extra. This is correct and lets the offline slice run from a clean clone with zero API keys.
- **Composition root**: `service.py:build_engine` is the single entrypoint used by CLI, `server/sessions`, and `benchmarks/runner`. `server/sessions.build_session_config` adds tenant pinning + a deterministic default embedding model per provider (lines 42-46) so ingest and chat resolve the same dim → collection. Good.
- **Engine cache**: `server/sessions._engine_cache` keyed by a config signature string (`_signature`, lines 125-139). Thread-safe via `_lock`. `reset_cache()` exists for tests.

Issues:
1. **Two SQLite databases with hardcoded paths** (P2):
   - `accounts/db.py:14` `DEFAULT_DB = "reports/raglab_app.db"` (overridable via `RAGLAB_APP_DB`).
   - `experiments/store.py:14` `DEFAULT_DB = "reports/experiments.db"` (no env override seen).
   - `ingestion/store.py` reuses `accounts.db.db_path()` — so the document catalog lives in the *accounts* DB, not its own. This is the source of the `ingestion → accounts` coupling. Three persistence concerns (app state, experiments, doc catalog) in two files with two different env-var conventions. Consolidate the path resolution.
2. **`benchmarks/runner.py` reaches into `core.config.build_llm`** (line 23) instead of going through `build_components`. It constructs a judge LLM separately and wraps it in `MeteredLLM`. This is a legitimate second composition path (judge LLM ≠ answer LLM) but it bypasses the central `build_components`, so it won't pick up future wiring changes there. Acceptable but document it.
3. **No god-objects.** `MemoryManager` (`memory/manager.py`, 160 lines) is the largest single class and is a facade over `sqlite` + `index` + `stores` + `formation` + `lifecycle` — correctly decomposed. `ExperimentConfig` is a Pydantic model with 11 nested config sections, which is configuration, not a god-object.

## Dead Code, Duplication, Orphans

1. **`pipelines/stubs.py`** (P1) — `_PLANNED = {}` empty dict, registration loop over nothing. Pure scaffolding. Delete until a planned architecture actually needs registering; the mechanism is 4 lines and trivially re-added.
2. **`backend.log` (5.6K) and `nohup.out` (597B) at repo root** (P2 — already mitigated). `.gitignore` now lists `*.log` and `nohup.out` (lines 28-29), and commit `2069d2c` "untrack stray runtime logs" removed them from tracking. The files still exist on disk but are ignored. Safe to `rm` from the working tree for cleanliness; no code references them.
3. **`uploads/` and `graphify-out/` at repo root** — both gitignored (`.gitignore:25,22`). `uploads/default/` exists on disk (runtime upload target). Not a code issue.
4. **Duplicated prompt-construction logic** (P2, minor): `pipelines/base.py:44` `_generate` calls `self.c.llm.generate(build_messages(...))` and `pipelines/helpers.py:24` `generate()` does the same thing. `helpers.generate` is a function-level mirror of `BasePipeline._generate`. Some pipelines use `helpers`, some use `self._generate`. Pick one; the `helpers` version is more reusable (no `self` needed) but `_generate` is the OOP version. Not a bug — they produce identical output — but two ways to do one thing.
5. **No duplicated retriever/embedder/LLM logic found.** Each provider adapter is thin and delegates to its SDK. `openai_compat.py` correctly shares the OpenAI+OpenRouter implementation via a private `_OpenAICompatLLM` base with two registered subclasses differing only in `_default_model`/`_base_url`/`_api_key_env`. Good deduplication.
6. **`memory/stores.py` is 210 lines for 10 classes**, most of which are 2-line specializations of `BaseMemoryStore` (set `type` + `semantic`). This is the right level of factoring — the shared behavior is in `base.py`, the specializations add domain helpers (`record_episode`, `save_playbook`, `set_pref`). Not duplication.

## Recommended Restructuring (concrete proposed target layout, minimal, prioritized P0/P1/P2)

The codebase is already well-structured. These are refinements, not rewrites. Ordered by value-to-effort.

### P0 — do now (small, high signal)
1. **Delete `src/raglab/pipelines/stubs.py`** and its import line in `src/raglab/pipelines/__init__.py:17`. Empty scaffolding. Re-add the 4-line mechanism when a stub is actually needed.
2. **`rm backend.log nohup.out`** from the working tree. Already gitignored; just tidy the disk.
3. **Route `routers/query.py` through `server.sessions`** (or document why not). Replace its `load_config` + `apply_overrides` + `build_engine` block (lines 47-52) with `build_session_config(tenant_id=..., config_path=req.config, overrides=req.overrides)` + `get_engine`, matching `chat.py`. This unifies engine lifecycle and gets tenant-pinned collections for free. Touches `src/raglab/routers/query.py` only.

### P1 — this restructuring pass
4. **Move `errors.py` into `core/`** as `src/raglab/core/errors.py`, update the two importers (`core/registry.py:80`, `core/config.py:19`) plus `api.py`, `cli.py`, `routers/*`, `server/*`, `benchmarks/runner.py`, `evaluation/*`, `llms/*`, `embeddings/*`. Blast radius is wide (errors is imported everywhere) but mechanical. Eliminates the `core → raglab` upward reach. Keep a one-line `src/raglab/errors.py` re-export shim if you want to avoid touching all importers at once.
5. **Resolve the `ingestion → accounts` coupling.** Pick one:
   - **(a) Move the document catalog into `accounts/`** as `src/raglab/accounts/documents.py` (it is per-tenant user-owned state, mirroring `conversations.py`). `routers/documents.py` already imports `accounts` — this tightens cohesion. Touches: new `accounts/documents.py` (from `ingestion/store.py`), `routers/documents.py:21-22`, delete `ingestion/store.py`.
   - **(b) Extract a shared DB path helper** into `src/raglab/core/persist.py` with `app_db_path()` / `experiments_db_path()`, and have `accounts/db.py` + `experiments/store.py` + the moved catalog all call it. Touches `accounts/db.py`, `experiments/store.py`, `ingestion/store.py`.
   Option (a) is cleaner — the catalog is tenant-scoped application state, not an ingestion concern. The CLI `ingest` path does not use this store at all (`cli.py` → `IngestionPipeline` → `vectorstores` only), so moving it out of `ingestion/` changes nothing for the CLI.
6. **Rename LLM adapter files for symmetry with embeddings/rerankers.** `llms/openai_compat.py` → `llms/openai_llm.py` + split `OpenRouterLLM` into `llms/openrouter_llm.py` (it's 14 lines of overrides). `llms/echo.py` → `llms/echo_llm.py`, `llms/gemini_llm.py` stays. Update `llms/__init__.py`. Mechanical; no public API change (registry names unchanged).

### P2 — consider, lower urgency
7. **Rename `ingestion/store.py` → `ingestion/catalog.py`** and `experiments/store.py` → `experiments/catalog.py` to disambiguate from `vectorstores`/`memory` stores. Only if you do P1.5; otherwise the move handles it.
8. **Consolidate the two prompt/generate helpers.** Either drop `pipelines/base.py:_generate` and have pipelines use `pipelines/helpers.generate`, or drop `helpers.generate` and keep `_generate`. 13 pipeline files import one or the other; check which is used more and keep that one. Touches `pipelines/base.py`, `pipelines/helpers.py`, and whichever pipeline files use the loser.
9. **Separate `api/` from `server/` only if the team grows.** Right now `server/` holds both the FastAPI wiring helpers (`sessions`, `deps`, `streaming`, `state`) and is the layer routers call. A cleaner split would be `api/routers/` (the HTTP surface, currently `routers/`) over `server/` (composition + wiring helpers). But this is a rename for clarity, not a correctness fix, and the current layout works. Skip unless you're already restructuring.
10. **Do NOT merge `retrievers` + `rerankers` + `vectorstores` into a `retrieval/` package.** They are separate registry kinds with separate contracts in `core/interfaces.py`; merging them adds import noise for no decoupling gain. The current per-kind packages are idiomatic for a plug-and-play framework.

## Risk & Dependency Impact (what breaks if we rename/restructure, blast radius)

| Change | Files touched | Risk | Mitigation |
|---|---|---|---|
| P0.1 delete `pipelines/stubs.py` | `pipelines/stubs.py`, `pipelines/__init__.py` | None — empty loop, no runtime effect | Verify `registry.available("architecture")` unchanged in `test_registry.py` |
| P0.2 rm logs | working tree only | None — already gitignored | — |
| P0.3 `query.py` via `sessions` | `routers/query.py` | Low — `/query` gains tenant pinning + cache; behavior change is that collection name becomes tenant-scoped. If `/query` callers expect a fixed `collection`, they break. | Check `test_enterprise.py` / `test_end_to_end.py` for `/query` usage; add `tenant_id` from `current_user` (optional_user if /query should stay open). |
| P1.4 move `errors.py` → `core/errors.py` | ~20 files import `raglab.errors` | Low but wide — pure rename, mechanical | Leave `src/raglab/errors.py` as a re-export shim (`from raglab.core.errors import *`) to do it incrementally |
| P1.5 move `ingestion/store.py` → `accounts/documents.py` | `routers/documents.py`, `ingestion/store.py` (moved) | Low — only `routers/documents.py` imports it today | Confirm no other importer (`grep "ingestion.store"` → only `routers/documents.py`) |
| P1.6 rename `llms/openai_compat.py` → `openai_llm.py` + `openrouter_llm.py` | `llms/__init__.py`, the two files | None — registry names (`openai`, `openrouter`) unchanged | Update `llms/__init__.py` imports |
| P2.7 rename `experiments/store.py` → `catalog.py` | `routers/query.py:19`, `benchmarks/runner.py:225` | Low — two importers | Mechanical |
| P2.8 consolidate generate helpers | `pipelines/base.py`, `pipelines/helpers.py`, ~13 pipeline files | Medium — every pipeline file changes; must verify each still calls the right helper | Grep `from raglab.pipelines.base import` vs `from raglab.pipelines.helpers import` per file; do one migration at a time |

**What does NOT break:** the registry seam means any rename of *files* under `embeddings/`, `llms/`, `retrievers/`, `rerankers/`, `vectorstores/`, `pipelines/`, `memory/` only affects that package's `__init__.py` (the side-effect import list). No business code imports these modules directly. This is why P1.6 is near-zero-risk.

**Test coverage of the change surface** (`tests/`):
- `tests/unit/test_registry.py` (27 lines) — covers `register`/`create`/`bootstrap`.
- `tests/unit/test_config.py` (38 lines) — covers `load_config` + overrides.
- `tests/unit/test_enterprise.py` (193 lines) — covers `server.sessions`, `accounts.auth`, `api` app, conversations. This is the guardrail for P0.3 and P1.5.
- `tests/unit/test_errors.py` (91 lines) — covers `call_with_retries` + error mapping. Guardrail for P1.4.
- `tests/unit/test_memory.py` (168 lines) — covers `MemoryManager`, stores, recall, lifecycle.
- `tests/unit/test_phase2_6.py` (78 lines) — covers pipelines (phase 2 + 6 architectures).
- `tests/unit/test_fusion_and_costs.py` (27 lines) — RRF + `cost_usd`.
- `tests/unit/test_chunkers.py` (20 lines) — chunkers.
- `tests/integration/test_end_to_end.py` (106 lines) — full ingest → query → benchmark.

**Coverage gaps** (no test imports these):
- `routers/query.py` `/query` and `/benchmark` endpoints are not directly tested (only `/chat/stream` and auth flows are in `test_enterprise.py`).
- `ingestion/store.py` (the document catalog) has no test.
- `graph/` (neo4j + networkx stores) — `test_phase2_6.py` imports `graph.store.NetworkXGraphStore` but there's no dedicated graph test.
- `evaluation/llm_judges.py` + `evaluation/ragas_eval.py` — no test imports (ragas is behind the `eval` extra).
- `observability/tracer.py` — no test.
- `server/streaming.py` SSE format — covered indirectly via `test_enterprise.py` chat flow, but no dedicated SSE-event-order test.

Add a `tests/unit/test_routers_query.py` before doing P0.3, and a `tests/unit/test_ingestion_store.py` (or `test_accounts_documents.py` after P1.5) before P1.5.