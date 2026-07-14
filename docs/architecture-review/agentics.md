# Agentics & RAG Core Architecture Review

Scope: `src/raglab/{agents, pipelines, memory, benchmarks, evaluation, graph, retrievers, rerankers, embeddings, vectorstores, llms, ingestion, routers, core}`. The FastAPI `server/`/`routers` HTTP layer and the `web/` frontend are out of scope; coupling to them is noted where it affects the core.

Every claim below is backed by a file path. Where the code is already good, that is stated explicitly.

---

## Swappable Component Architecture (interfaces, registry, config, factory)

This is the central question. Verdict: **the core mechanism is clean, consistent, and honestly applied to seven of the nine swappable kinds. The remaining two (cleaners, evaluators) bypass it, and a few subsystem protocols live outside `core/`.**

### The contract — `src/raglab/core/interfaces.py`

Eleven `@runtime_checkable` Protocols in one file: `Parser`, `Chunker`, `Embedder`, `VectorStore`, `Retriever`, `Reranker`, `LLM`, `Pipeline`, `Evaluator`. They depend only on `core/types.py` (Chunk, Document, LLMResponse, RAGResult, ScoredChunk, Vector). No provider coupling. This is exactly right.

### The registry — `src/raglab/core/registry.py`

A two-level `dict[kind][name] -> class`, a `@register(kind, name)` class decorator, `bootstrap()` which imports a fixed tuple `_IMPL_PACKAGES` so registrations fire, and `create(kind, name, **kwargs)` which instantiates. Duplicate registration raises. Lazy heavy imports live inside `__init__`/methods, so importing the package never requires `torch`/`openai`. ~90 lines. Simple, no metaclass magic. Good.

`_IMPL_PACKAGES` lists: `ingestion.parsers`, `ingestion.chunkers`, `embeddings`, `vectorstores`, `retrievers`, `rerankers`, `llms`, `pipelines`, `evaluation`, `observability`, `graph`, `memory.stores`.

### The composition root — `src/raglab/core/config.py`

Pydantic `ExperimentConfig` with nested cfg models (`EmbeddingCfg`, `ChunkerCfg`, `VectorStoreCfg`, `RetrievalCfg`, `RerankerCfg`, `LLMCfg`, `AgentCfg`, `GraphCfg`, `ObservabilityCfg`, `EvaluationCfg`). `build_*` functions resolve each section via `registry.create(...)`. `build_components` returns a `Components` dataclass; `build_pipeline_from_components` resolves the architecture. There is an embedding allow-list (`_EMBEDDING_NAMES`) so `openrouter` (chat-only) is rejected at config time. Swapping any component is a YAML edit. This is the factory. Good.

### One impl of each — pattern consistency

| Kind | File | Decorator | Pattern match |
|---|---|---|---|
| embedder | `embeddings/openai_embed.py` | `@register("embedder", "openai")` | yes |
| vectorstore | `vectorstores/qdrant_store.py` | `@register("vectorstore", "qdrant")` | yes |
| retriever | `retrievers/dense.py`, `bm25.py`, `hybrid.py`, `compressed.py`, `multi_query.py` | `@register("retriever", ...)` | yes |
| reranker | `rerankers/cross_encoder.py` | `@register("reranker", "cross_encoder")` | yes |
| llm | `llms/openai_compat.py` | `@register("llm", "openai")` / `"openrouter"` | yes |
| parser | `ingestion/parsers/text.py` | `@register("parser", "text")` | yes |
| chunker | `ingestion/chunkers/recursive.py` | `@register("chunker", "recursive")` | yes |
| architecture | `pipelines/naive.py` etc. | `@register("architecture", "naive_rag")` | yes (uses kind `architecture`, not `pipeline`) |

Every impl uses `**_: object` to tolerate extra kwargs, lazy-imports heavy deps in `_ensure()`, and raises `MissingDependencyError`/`ProviderAuthError` from `errors.py`. The pattern is consistent and disciplined.

### Where the pattern breaks

1. **Cleaners are not a component** (`ingestion/cleaners/__init__.py`). `clean_text`/`clean_documents` are plain functions, no Protocol, no `@register`. `IngestionPipeline.ingest` hardcodes `clean_documents` (`ingestion/pipeline.py:60`). Not swappable via YAML. This is the one place the "swappable component" story is silently violated.
2. **Evaluators are not registered** (`evaluation/`). `core/interfaces.py` declares an `Evaluator` Protocol, but `evaluation/llm_judges.py::LLMJudge`, `evaluation/ragas_eval.py::RagasEvaluator`, and `evaluation/builtin.py::evaluate_builtin` are **not** `@register`ed. `benchmarks/runner.py` imports them directly (`from raglab.evaluation.ragas_eval import RagasEvaluator`, `from raglab.evaluation.llm_judges import LLMJudge`). There is no `build_evaluator(cfg)` and no `evaluator` kind in `_IMPL_PACKAGES`. The Protocol is effectively dead. `evaluation/__init__.py` imports only `builtin, reports` (not even `llm_judges`/`ragas_eval`), so the package import doesn't even side-effect-register anything.
3. **Subsystem-local protocol definitions** (see Naming section). `MemoryStore` in `memory/interfaces.py`, `GraphStore` in `graph/__init__.py`, `Tracer` in `observability/tracer.py`. Defensible for `MemoryStore` (memory is a big subsystem); less so for `GraphStore` and `Tracer`, which are small enough to live in `core/interfaces.py` for discoverability. `GraphStore` is registered as kind `graphstore` (consistent with the central registry), `Tracer` is built via `build_tracer(cfg)` factory (not registered).
4. **`build_retriever` hardcodes the retriever wiring** (`core/config.py:179-221`). A `if cfg.type == "dense"/"bm25"/"compressed"/"hybrid"/"multi_query"` ladder with bespoke constructor kwargs for each. Adding a new retriever requires editing this function, not just registering. The other `build_*` functions are one-liners; this one is the exception. Minor, but it's the one place the factory knows about concrete kinds.

---

## Pipeline Abstractions (BasePipeline + Adaptive/Advanced/Agentic)

`pipelines/base.py::BasePipeline` is intentionally tiny: holds `self.c: Components`, exposes `name`, a `_generate(query, contexts, metrics)` helper, and module-level `SYSTEM_PROMPT`/`format_context`/`build_messages`. `pipelines/helpers.py` adds shared `retrieve/rerank/generate/generate_with_instruction/expand_parents/dedup`. Thirteen architectures, each `@register("architecture", <name>)`, each overrides `run(query) -> RAGResult`. Shared types (`RAGResult`, `RunMetrics`, `TrajectoryStep`, `timer`) from `core/types.py`.

**This is a clean strategy pattern, not a chain-of-responsibility.** Each pipeline is a leaf strategy selected by config; `AdaptiveRAG` is the only router (delegates to `naive_rag`/`hybrid_rag`/`agentic_rag` based on `reasoning.classify_complexity`). `AgenticRAG` is the only LangGraph state machine; the rest are procedural. The shared plumbing (`helpers.*`, `BasePipeline._generate`, `build_messages`, `timer`) is genuinely shared.

### Divergence / smells (concrete)

- **Three generate wrappers.** `BasePipeline._generate` (`pipelines/base.py:44`), `helpers.generate` (`pipelines/helpers.py:24`), and `AgenticRAG._generate` (`pipelines/agentic.py:96`, inlined, ignores `BasePipeline._generate`). `NaiveRAG`/`HybridRAG` use `self._generate`; Phase-3 architectures use `helpers.generate`; `AgenticRAG` inlines its own. Three paths to "build messages + call llm + add_llm". Should be one.
- **`pipelines/stubs.py` is dead scaffolding.** `_PLANNED: dict = {}` and a `_make_stub` factory that loops over an empty dict. Registers nothing. The docstring claims Phase 2/3 are "now implemented in their own modules" — so this file is a leftover. Delete it.
- **`AgenticRAG` redefines `_generate` with a different signature** (`_generate(self, state: AgentState) -> AgentState` vs `BasePipeline._generate(self, query, contexts, metrics) -> LLMResponse`). Name collision across the inheritance line. The LangGraph node method should be named `_generate_node` or similar.
- **Config coupling is fine but asymmetric.** `AgenticRAG`, `CRAG`, `SelfRAG`, `ReflectiveRAG`, `DeepSearchRAG` all reach into `self.c.config.agent.grade_threshold` / `max_retrieval_retries`. `agent` config is shared by both the LangGraph loop and the procedural corrective pipelines. Acceptable.
- **`AdaptiveRAG` uses `registry.create("architecture", target, components=self.c)` to delegate** (`pipelines/adaptive.py:22`). Clean — no import of concrete pipeline classes. Good.
- **`graph_rag.py::build_graph` is a free function** that `kg_vector_rag.py` imports. Slightly awkward cross-pipeline import; could be a helper.

### What is good

- `RAGResult` is the uniform output; `architecture` field self-labels; `trajectory` is appended uniformly; `metrics` accumulates cost/tokens/latency via `timer` + `add_llm`. Benchmark runner and evaluators consume `RAGResult` cleanly.
- `helpers.py` keeps each architecture file focused on its distinctive control flow.
- `AgenticRAG.attach_memory` is an opt-in hook (default off, tests unchanged). Coupling to memory is a single lazy import inside two methods.

---

## Memory Subsystem

`memory/manager.py::MemoryManager` is the single entrypoint. Ten memory types in `memory/stores.py`, each `@register("memory", <type>)`, each a thin specialization of `memory/base.py::BaseMemoryStore` (differs by `type` and `semantic` flag, plus a few domain helpers: `record_episode`, `save_playbook`, `set_pref`/`get_pref`, `save_state`/`load_state`/`checkpoint`, `add_relation`/`neighbors`/`traverse`). `BaseMemoryStore` handles SQLite (`memory/backends/sqlite_store.py`) + optional Qdrant vector projection (`memory/backends/vector_index.py`). `memory/scoring.py` (importance, recency, combined), `memory/formation.py` (write gate), `memory/lifecycle.py` (TTL/decay/prune/dedup). `MemoryScope` (tenant/user/agent/session) for isolation + governance + GDPR erase.

### Coherence vs over-engineering

- **Coherent and well-layered.** `BaseMemoryStore` is the right abstraction; the 10 types are mostly 3-5 lines of specialization. `MemoryManager` exposes `remember/recall/forget/consolidate/timeline/stats/audit/maintain/erase` — a coherent API surface.
- **Two of ten types have no consumers.** `WorkflowMemory` (`memory/stores.py:128`) — `save_state`/`load_state`/`checkpoint` are defined but no pipeline or agent calls them (confirmed: no external import). `GraphMemory` (`memory/stores.py:160`) — `add_relation`/`neighbors`/`traverse` build a networkx graph on demand; also no external consumer. These are speculative. Not harmful, but they are YAGNI until a pipeline uses them.
- **`GraphMemory._graph` rebuilds a networkx graph from SQLite rows on every call** (`memory/stores.py:181-189`). No caching. This is a known ceiling that should carry a `ponytail:` comment naming the upgrade path (cache per scope, invalidate on add).
- **Coupling to pipelines/agents is minimal and opt-in.** Only `AgenticRAG` uses memory, via `attach_memory` + two private methods (`pipelines/agentic.py:53,192-211`). The imports of `MemoryQuery`/`Episode` are lazy (inside methods). `# type: ignore` annotations reflect the optional wiring. Clean.
- **`MemoryStore` Protocol lives in `memory/interfaces.py`, not `core/interfaces.py`.** Defensible — memory is a subsystem with its own types. But it is a second interface-definition site; see Naming.

### What is good

- `MemoryScope` is a clean isolation primitive reused by every store, the lifecycle engine, and the audit log.
- `formation` gate prevents dumping trivial content; `lifecycle` keeps memory bounded; both use the same `scoring` primitives. Good separation.
- SQLite is source of truth; Qdrant is a rebuildable derived projection (`memory/backends/vector_index.py:2`). Correct architecture.

---

## Agents & Reasoning

`agents/` contains four files: `grading.py` (`GradeResult`, `grade_retrieval`, `_content_tokens`), `critic.py` (`CritiqueResult`, `critique_answer`, `attach_citations`), `rewrite.py` (`rewrite_query`), `reasoning.py` (`classify_complexity`, `decompose`, `identify_gaps`). These are **pure functions and small dataclasses**, not classes, not LangGraph nodes. They are consumed by `agentic.py`, `crag.py`, `self_rag.py`, `reflective.py`, `adaptive.py`, `advanced.py`, `deep_search.py`, `multi_hop.py`.

### Naming: `agents/` is a misnomer

The package is really "shared reasoning heuristics + agent-node bodies". The actual agent — the LangGraph state machine with `plan/retrieve/grade/rewrite/generate/critic/cite` nodes — lives in `pipelines/agentic.py`. `agents/` holds the callable logic those nodes invoke, but it is also imported by non-agentic pipelines (CRAG, Self-RAG, Reflective, Advanced, DeepSearch, MultiHop, Adaptive). A better name is `reasoning/` or `agent_nodes/`; the current name implies the agent runtime lives there, which it does not.

### Coupling

- `agents/grader._content_tokens` is imported by `critic.py`, `reasoning.py`, `pipelines/crag.py`, `pipelines/self_rag.py` (5 modules). A leading-underscore "private" name is the de-facto shared text utility. Should be public (`content_tokens`) and ideally live in a shared `core/text.py` — `evaluation/builtin.py` has a near-identical `_TOKEN`/`_STOP` copy.

### Dead parameters

- `reasoning.classify_complexity(query, llm=None)` and `reasoning.decompose(query, max_subs=3, llm=None)` accept an `llm` kwarg and never use it (`agents/reasoning.py:19,39`). The docstring promises an upgrade path that was never wired. Either wire it or drop the param. `adaptive.py` passes `self.c.llm` to `classify_complexity`; `multi_hop.py` passes `self.c.llm` to `decompose`. Callers believe the param does something.

### What is good

- Every heuristic has a deterministic offline default so the whole platform runs without an LLM. The `llm` param (where it would be used) is a clean seam for upgrade.
- `GradeResult`/`CritiqueResult` are small dataclasses carrying `score`/`reason`/`ok` — pipelines record them in `TrajectoryStep` cleanly.

---

## Evaluation & Benchmarks

### Types are shared cleanly

`RAGResult`, `RunMetrics`, `TrajectoryStep` from `core/types.py` flow through `Engine.answer` (`service.py:41`) → `benchmarks/runner.py:174` converts to record dicts `{question, answer, contexts, ground_truth}` for evaluators. No duplicate result types in evaluation.

### The evaluation component pattern is incomplete

- `core/interfaces.py::Evaluator` Protocol (`evaluate(records: list[dict]) -> dict[str,float]`) is satisfied structurally by `LLMJudge.evaluate` and `RagasEvaluator.evaluate`, but **neither is `@register`ed** and **`evaluate_builtin` is a function, not a class** (doesn't fit the Protocol). `benchmarks/runner.py` imports each evaluator directly and orchestrates them by hand (`_evaluate`, lines 85-137). The `Evaluator` Protocol is dead code; the runner is the de-facto factory.
- `evaluation/__init__.py` imports only `builtin, reports` — not `llm_judges`, `ragas_eval`. So importing the package doesn't even surface the LLM-backed evaluators. (They are lazy-imported by the runner, which is fine for deps, but inconsistent with the other packages' "import everything to register" pattern — except here there's nothing to register.)

### Benchmark runner — `benchmarks/runner.py`

Matrix expander (`expand_matrix`), per-cell config build, ingestion, answer loop, metric aggregation, CSV+HTML reports, SQLite experiment persistence (`experiments/store.py`). Isolates each evaluator in try/except so one failing judge doesn't abort the matrix. Ranks by the first builtin metric. This is well-built.

### Smell

- `_deep_merge` is defined twice: `core/overrides.py:32` and `benchmarks/runner.py:33`. Two copies of the same function.

### Experiments store — `experiments/store.py`

SQLite table with config summary + `metrics_json` blob + cost/latency. `save_experiments`/`list_experiments`. Simple, fine. The schema duplicates the row keys in `_CORE` and in the `INSERT` statement — minor.

---

## Graph Store

`graph/__init__.py` declares the `GraphStore` Protocol and imports `store, neo4j_store` (which `@register("graphstore", ...)`). `graph/store.py::NetworkXGraphStore` (in-core default), `graph/neo4j_store.py::Neo4jGraphStore` (lazy driver), `graph/extract.py` (heuristic entity/relation extraction — capitalized phrases + acronyms, co-occurrence relations).

### Coupling

Consumed only by `pipelines/graph_rag.py` and `pipelines/kg_vector_rag.py` via `build_graph(components)` → `store.build_from_chunks(components.store.all_chunks())` → `entity_search`/`multi_hop`. The graph is built from the vector store's chunks, so no separate ingestion. Standalone-able but currently only the two graph pipelines use it. No coupling to memory.

### Smells

- **Protocol vs implementation divergence.** `GraphStore.build(docs: list[Document])` is the declared Protocol method. Both stores implement `build(docs)` as a thin convenience wrapper that delegates to `build_from_chunks(chunks)` (`graph/store.py:37-39`, `graph/neo4j_store.py:62-65`). The pipelines call `build_from_chunks` directly. So the Protocol surface and the real call path don't match. Either the Protocol should declare `build_from_chunks`, or the pipelines should call `build`.
- **`Neo4jGraphStore.communities()` returns `[]`** (`graph/neo4j_store.py:112`). Declared in the Protocol, unimplemented. Should raise `NotImplementedError` or be dropped from the Protocol.
- **Naming collision with memory's `graph` type.** `memory/stores.py::GraphMemory` (`register("memory", "graph")`) is a separate concept (relations as memory records with on-demand networkx traversal). It is not a `GraphStore`. Two "graph" concepts in two packages. Not a bug, but a reader will confuse them. `graph/` is the KG store; `memory/...graph` is relational memory. Worth a docstring cross-reference.
- **`graph_rag.py::build_graph` is a module-level function imported by `kg_vector_rag.py`.** Cross-pipeline import. Minor.

### What is good

- Heuristic extractor is deterministic and offline; an `llm` extractor is the documented upgrade seam.
- The networkx store records which chunk ids each entity appears in, so graph traversal returns real text via `ScoredChunk`. Clean.

---

## Naming & Duplication Findings (concrete, with paths)

1. **Interface-definition sites are split across four files.**
   - `core/interfaces.py` — Parser, Chunker, Embedder, VectorStore, Retriever, Reranker, LLM, Pipeline, Evaluator.
   - `memory/interfaces.py` — MemoryStore.
   - `graph/__init__.py` — GraphStore.
   - `observability/tracer.py` — Tracer.
   `MemoryStore` is justified (subsystem). `GraphStore` and `Tracer` are small enough to live in `core/interfaces.py` for discoverability. `GraphStore` is registered through the central registry (kind `graphstore`), so the only inconsistency is where the Protocol is textually defined.

2. **Naming convention is consistent.** All interfaces are `Protocol` (no `Base*`/`I*`/`*Interface` mix). `BaseMemoryStore` and `BasePipeline` are concrete shared base classes, not protocols — correct. No parallel hierarchies for the same concept.

3. **`agents/` is a misnomer.** It holds shared reasoning heuristics consumed by both the agentic LangGraph loop and seven non-agentic pipelines. The agent runtime lives in `pipelines/agentic.py`. Better: `reasoning/` or `agent_nodes/`.

4. **`_content_tokens` is a private-named public utility** (`agents/grading.py:22`), imported across 5 modules (`agents/critic.py`, `agents/reasoning.py`, `pipelines/crag.py`, `pipelines/self_rag.py`, and internally in `grading.py`). Rename to `content_tokens`.

5. **Duplicate tokenizer/stopword set.** `agents/grading.py::_TOKEN`/`_STOP` and `evaluation/builtin.py::_TOKEN`/`_STOP` are near-identical copies. Extract to `core/text.py` (or `core/text_utils.py`) and reuse from both.

6. **Duplicate `_deep_merge`.** `core/overrides.py:32` and `benchmarks/runner.py:33`. Two copies of the same recursive merge. Move to `core/config.py` or a `core/utils.py` and import from both.

7. **Three "generate" wrappers.** `BasePipeline._generate` (`pipelines/base.py:44`), `helpers.generate` (`pipelines/helpers.py:24`), `AgenticRAG._generate` (`pipelines/agentic.py:96`). Plus `helpers.generate_with_instruction`. Collapse to one (plus the `_with_instruction` variant).

8. **Dead `pipelines/stubs.py`.** `_PLANNED = {}`; registers nothing. Delete the file (and its import in `pipelines/__init__.py`).

9. **Dead `llm` parameters.** `agents/reasoning.py:classify_complexity` and `decompose` accept `llm` and ignore it. Callers (`adaptive.py:22`, `multi_hop.py:22`) pass `self.c.llm`. Wire or drop.

10. **Dead `Evaluator` Protocol.** `core/interfaces.py:107` declares it; nothing `@register`s as `evaluator`; the benchmark runner imports evaluators directly. Either register `LLMJudge`/`RagasEvaluator` and add a `build_evaluator(cfg)` to `core/config.py`, or delete the Protocol and document that evaluation is runner-orchestrated.

11. **`evaluation/__init__.py` import is incomplete.** Imports `builtin, reports` only; `llm_judges` and `ragas_eval` are not imported anywhere at package load (only lazy in the runner). If the intent is "importing the package registers everything", this breaks the pattern. If evaluators are never registered, this is consistent-but-different. Pick one story.

12. **`GraphStore` Protocol `build(docs)` vs the real `build_from_chunks(chunks)` entry point.** Pipelines call `build_from_chunks`; the Protocol declares `build`. Align them.

13. **`Neo4jGraphStore.communities()` returns `[]` silently** (`graph/neo4j_store.py:112`). Either raise or drop from the Protocol.

14. **Unused memory types.** `WorkflowMemory` (`memory/stores.py:128`) and `GraphMemory` (`memory/stores.py:160`) have no consumers outside their own file. YAGNI until a pipeline uses them.

15. **`build_retriever` is a hardcoded ladder** (`core/config.py:179-221`). Every other `build_*` is a one-liner over `registry.create`; this one knows each retriever's constructor shape. Adding a retriever means editing this function. Minor, but the one place the factory isn't uniform.

16. **`service.py` is a flat module at `src/raglab/service.py`** (not a package). It holds `Engine` + `build_engine`, the composition shared by CLI, API, and benchmark runner. Fine, but it sits alongside `server/` (a package) and `routers/` (a package). Slight structural asymmetry.

---

## Recommended Restructuring (concrete target layout, minimal, P0/P1/P2)

The core is mostly right. Do not undertake a big-bang move. The following are surgical.

### P0 — cheap wins, no behavior change

1. **Delete `pipelines/stubs.py`** and remove its import in `pipelines/__init__.py:17`. Dead code.
2. **Rename `_content_tokens` → `content_tokens`** in `agents/grading.py` and its 5 importers. Private name used publicly.
3. **Extract `core/text.py`** with `content_tokens(text) -> set[str]` + the shared `_TOKEN`/`_STOP`. Reuse from `agents/grading.py` and `evaluation/builtin.py`. Delete the two copies.
4. **Extract `core/utils.py::deep_merge`** (or add to `core/config.py`). Reuse from `core/overrides.py` and `benchmarks/runner.py`. Delete the two copies.
5. **Drop the dead `llm` param** from `reasoning.classify_complexity` and `reasoning.decompose` (or wire it — but wiring is P2). Update `adaptive.py` and `multi_hop.py` callers.
6. **Fix `Neo4jGraphStore.communities()`** to `raise NotImplementedError` or remove from `GraphStore` Protocol.
7. **Align `GraphStore` Protocol** with the real entry point: declare `build_from_chunks(chunks: list[Chunk])` (keep `build(docs)` as a convenience if desired, but the Protocol should name what callers use).

### P1 — consistency, slightly larger

8. **Collapse the three generate wrappers.** Keep `helpers.generate` and `helpers.generate_with_instruction`; have `BasePipeline._generate` delegate to `helpers.generate`; rename `AgenticRAG._generate` to `_generate_node` and have it call `helpers.generate`. One path.
9. **Move `GraphStore` Protocol into `core/interfaces.py`** (keep the impls in `graph/`). `Tracer` can stay in `observability/` (it's a subsystem with its own config). `MemoryStore` stays in `memory/interfaces.py`.
10. **Rename `agents/` → `reasoning/`.** Update the 9 importers (`pipelines/{agentic,crag,self_rag,reflective,adaptive,advanced,deep_search,multi_hop,graph_rag?}`). Add a compatibility shim `agents/__init__.py` re-exporting for one release if external consumers exist.
11. **Resolve the `Evaluator` story.** Either:
    - (a) Register `LLMJudge` and `RagasEvaluator` via `@register("evaluator", ...)`, wrap `evaluate_builtin` in a small `BuiltinEvaluator` class, add `build_evaluator(cfg)` to `core/config.py`, and have the benchmark runner use `registry.create`; or
    - (b) Delete the `Evaluator` Protocol and document that evaluation is runner-orchestrated.
    Recommendation: (a) — it's a small amount of code and completes the swappable-component story.
12. **Add a `cleaner` kind.** Define a `Cleaner` Protocol in `core/interfaces.py` (`clean(docs: list[Document]) -> list[Document]`), `@register("cleaner", "default")` on the existing `clean_documents` (wrapped as a class), and a `build_cleaner(cfg)` so `IngestionPipeline` gets it from config instead of hardcoding `clean_documents`. Lets users disable/swap cleaning via YAML.

### P2 — structural, only if the codebase grows

13. **Consider a `retrieval/` superpackage** grouping `retrievers/`, `rerankers/`, `embeddings/`, `vectorstores/` once the per-package `__init__.py` re-exports become noise. Not justified at current size (4-6 files each); the flat layout is fine.
14. **Consider splitting `rag/` (runtime) from `eval/` from `memory/`** at the top level if `pipelines/` + `agents/` + `ingestion/` grow further. Current `pipelines/` (17 files) is the borderline case; if it grows past ~25, split into `pipelines/rag/` and `pipelines/eval/` (the latter for any evaluation-driving pipelines, if they appear).
15. **`build_retriever` ladder** (`core/config.py:179-221`): if a 6th retriever is added, refactor to have each retriever register its own `build_from_config(cfg, embedder, store)` factory, so the composition root doesn't know concrete kinds. Not worth it at 5 retrievers.
16. **`WorkflowMemory` / `GraphMemory`**: either wire a consumer (a workflow-checkpoint pipeline, a relational-memory retrieval step) or remove them with a deprecation note. Keeping unused registered components invites confusion.

### Target layout (post-P0/P1)

```
src/raglab/
  core/
    interfaces.py   # +GraphStore, +Cleaner (P0/P1)
    types.py
    registry.py
    config.py       # +build_cleaner, +build_evaluator (P1)
    overrides.py
    text.py         # NEW (P0) — shared tokenizer
    utils.py        # NEW (P0) — deep_merge
  reasoning/        # renamed from agents/ (P1)
    grading.py
    critic.py
    rewrite.py
    reasoning.py
  pipelines/
    base.py
    helpers.py
    naive.py ... graph_rag.py   # (stubs.py deleted)
  memory/           # unchanged
  graph/            # impls stay; Protocol moves to core/
  evaluation/       # @register evaluators (P1)
  benchmarks/
  experiments/
  ingestion/
    cleaners/       # becomes a registered component (P1)
  ...
```

---

## Risk & Dependency Impact (blast radius)

| Change | Files touched | Importers to update | Risk |
|---|---|---|---|
| Delete `pipelines/stubs.py` (P0) | `pipelines/stubs.py`, `pipelines/__init__.py` | 0 | none — registers nothing, imports nothing used elsewhere |
| Rename `_content_tokens` (P0) | `agents/grading.py` + 4 importers | 4 | trivial, mechanical |
| Extract `core/text.py` (P0) | new file, `agents/grading.py`, `evaluation/builtin.py` | 2 | low; ensure identical token/stopword semantics (they are near-identical) |
| Extract `core/utils.py::deep_merge` (P0) | new file, `core/overrides.py`, `benchmarks/runner.py` | 2 | low; the two impls differ only in a `None`-skip detail in `overrides.py` — preserve it |
| Drop `llm` param from `reasoning` (P0) | `agents/reasoning.py`, `pipelines/adaptive.py`, `pipelines/multi_hop.py` | 2 callers | low; no behavior change (param was unused) |
| `Neo4jGraphStore.communities` raise (P0) | `graph/neo4j_store.py` | 0 (no caller) | none |
| Align `GraphStore` Protocol (P0) | `graph/__init__.py` (Protocol), `graph/store.py`, `graph/neo4j_store.py` | 0 (impls already have `build_from_chunks`) | low; add `build_from_chunks` to the Protocol signature |
| Collapse generate wrappers (P1) | `pipelines/base.py`, `pipelines/helpers.py`, `pipelines/agentic.py`, all Phase-3 pipelines (verify they still call `helpers.generate`) | ~8 | medium; behavior must stay identical — keep `generate_with_instruction` for CRAG/SelfRAG/Reflective |
| Move `GraphStore` Protocol to `core/interfaces.py` (P1) | `core/interfaces.py`, `graph/__init__.py`, any importer of `GraphStore` | check `graph_rag.py`, `kg_vector_rag.py` (they import `build_graph`, not the Protocol, directly) | low |
| Rename `agents/` → `reasoning/` (P1) | 9 pipeline files + `agents/__init__.py` | 9 | medium; add a shim `agents/__init__.py` re-exporting for one release; grep for `from raglab.agents` across `server/`, `routers/`, `cli.py`, tests |
| Register evaluators (P1) | `evaluation/llm_judges.py`, `evaluation/ragas_eval.py`, new `evaluation/builtin.py` class, `core/config.py`, `benchmarks/runner.py` | 1 (runner) | medium; `evaluate_builtin` is a function — wrapping it changes its call shape; `LLMJudge` already matches the Protocol |
| Add `cleaner` kind (P1) | `core/interfaces.py`, `core/config.py`, `ingestion/cleaners/__init__.py`, `ingestion/pipeline.py` | 1 (`ingestion/pipeline.py`) | low; default cleaner preserves current behavior |
| Remove `WorkflowMemory`/`GraphMemory` (P2) | `memory/stores.py`, `memory/types.py` (WorkflowState, Episode stay) | 0 confirmed consumers | low, but verify `server/`/`routers/` don't reference them via the memory API |

### Cross-cutting note (out of scope but affected)

- `server/sessions.py:149` and `routers/query.py:51` call `build_engine`; `cli.py:79` calls `build_engine`. The composition root (`core/config.py` + `service.py`) is the seam; none of the P0/P1 changes alter `build_engine`'s signature. P1 evaluator registration touches `benchmarks/runner.py` only.
- `accounts/db.py` is imported by `ingestion/store.py` for the document catalog SQLite path. Not in scope, but any move of `ingestion/` must preserve that.

### What is already good (do not touch)

- The `core/types.py` dataclasses, `core/registry.py`, `core/config.py` composition root, the `@register` discipline across retrievers/embedders/llms/vectorstores/rerankers/chunkers/parsers, the `RAGResult`/`RunMetrics`/`TrajectoryStep` contract, the `BasePipeline` strategy pattern, the `MemoryManager`/`BaseMemoryStore`/`MemoryScope` layering, the `GraphStore` registry integration, the lazy-import + `MissingDependencyError` discipline, and the `errors.py` retry/fatal/transient split. The architecture is fundamentally sound; the findings above are consistency cleanup, not redesign.