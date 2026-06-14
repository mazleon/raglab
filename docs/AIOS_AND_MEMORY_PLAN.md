# RAGLab → AI Operating System: Architecture & Implementation Plan

## Context

RAGLab today is a modular, tested Agentic RAG backend (13 architectures,
multi-provider, evaluation, observability, benchmarking). The next stage turns it
into a **Memory-Centric Agentic AI Operating System**: a Memory Engineering
Platform plus an Agentic Intelligence Workspace frontend.

This is a multi-quarter program. This document is the plan; **this branch
implements the Memory Engineering Platform backend** (the part that integrates
natively with the existing Python/registry architecture and is fully testable),
and specifies the frontend AIOS as the next workstream.

---

## Part A — Memory Engineering Platform (implemented in this branch)

### Goal
Treat memory as a first-class, pluggable subsystem alongside RAG. Ten memory
types, two storage tiers, lifecycle + governance, and native integration with
the agentic pipelines and the API.

### Storage model (SQLite + Qdrant)
- **SQLite = structured source of truth.** Every `MemoryRecord` is a row:
  content, type, scope (tenant/user/agent/session), importance, timestamps,
  access counts, TTL, structured payload (JSON). Powers exact/filtered queries,
  recency, temporal timelines, governance (GDPR delete by scope), and an
  append-only **audit log**.
- **Qdrant = semantic recall.** Records that benefit from similarity search are
  embedded and indexed with a flat payload (`memory_id`, `type`, scope) so recall
  can filter by type + tenant/user/agent/session. In-memory for tests, on-disk or
  server for production (same precedence as the RAG store).

A record's lifecycle: SQLite is authoritative; the vector index is a derived,
rebuildable projection. Deleting from SQLite cascades to Qdrant.

### Ten memory types (all `MemoryStore`-conforming, registry-pluggable)
| Type        | Backed by            | Purpose |
|-------------|----------------------|---------|
| `working`   | SQLite (+ summarize) | active session: task state, plan, tool outputs; short TTL, compression/pruning |
| `episodic`  | SQLite + Qdrant      | past experiences (goal/action/result/feedback); recall similar episodes |
| `semantic`  | SQLite + Qdrant      | facts/knowledge; vector + filter retrieval |
| `procedural`| SQLite + Qdrant      | workflows/playbooks/SOPs; retrieve by task similarity |
| `long_term` | SQLite               | durable user/project/org/agent preferences (key→value), survives sessions |
| `reflection`| SQLite + Qdrant      | what worked/failed/lessons; used by Self-RAG/critic |
| `agent`     | SQLite + Qdrant      | per-agent private memory + success/failure history (scope.agent_id) |
| `shared`    | SQLite + Qdrant      | team memory across agents in a session/tenant: evidence, conclusions |
| `workflow`  | SQLite               | goal/subtasks/deps/status/current state; checkpoint + resume |
| `graph`     | networkx (in-core)   | entity/relationship memory; multi-hop traversal (reuses GraphStore) |

### Cross-cutting engines
- **Scoring** (`scoring.py`): importance (signals → 0..1), exponential recency
  decay, freshness; combined recall score = `w_rel·relevance + w_imp·importance + w_rec·recency`.
- **Formation** (`formation.py`): `should_remember` (importance + near-duplicate
  gate) and **consolidation** (summarize working/episodic → long-term).
- **Lifecycle** (`lifecycle.py`): TTL expiry, decay, prune (low-importance/stale),
  dedup (embedding similarity).
- **Manager** (`manager.py`): one entrypoint — `remember`, `recall` (cross-type,
  fused + reranked by combined score), `forget`, `consolidate`, `timeline`,
  `stats`, and scope-based governance (isolation, GDPR delete, audit).

### Folder structure
```
src/raglab/memory/
  types.py              # MemoryRecord, MemoryScope, MemoryQuery, MemoryHit, Episode, WorkflowState
  interfaces.py         # MemoryStore protocol
  scoring.py            # importance / decay / recency / combined score
  backends/
    sqlite_store.py     # structured store + audit + governance
    vector_index.py     # Qdrant semantic index (scope/type filters)
  base.py               # BaseMemoryStore (SQLite + optional vector index)
  stores.py             # the 10 registered memory-type stores
  lifecycle.py          # decay / prune / dedup / TTL
  formation.py          # should_remember + consolidation
  manager.py            # MemoryManager (orchestration + governance)
```

### API (FastAPI, this branch)
```
POST   /memory/remember        {type, content, scope, importance?, structured?}
POST   /memory/recall          {query, scope, types?, k?}
GET    /memory/timeline        ?scope...&since&until
GET    /memory/stats           ?scope...
DELETE /memory/{id}            (single)            -> audit
DELETE /memory?scope...        (GDPR erase by scope) -> audit
```

### Agentic integration (non-breaking, opt-in)
The Agentic RAG loop can, when a `MemoryManager` is attached: recall similar past
**episodes** before planning, record an **episode** (query, trajectory, grade,
accepted) after answering, and write **reflection** memory on low grades. Default
off → existing behaviour and tests unchanged.

### Governance / multi-tenancy / observability
- Every record carries a `MemoryScope`; all queries filter by scope → tenant
  isolation. GDPR erase = delete-by-scope (SQLite cascade + Qdrant purge), logged.
- Append-only audit log (create/access/update/delete/prune) with actor + time.
- `stats` and `timeline` provide memory observability (counts by type, usage,
  evolution over time). Memory eval proxies: precision/recall/usefulness/freshness.

### Testing
Fully offline: temp SQLite + in-memory Qdrant + hashing embedder. Unit tests for
SQLite store, vector index, scoring, lifecycle, formation, each memory type, and
the manager; integration test for remember→recall→consolidate→govern and the API.

---

## Part B — Agentic Intelligence Workspace (frontend AIOS, next workstream)

> Specified here; **not** built in this branch (separate Next.js app, separate
> test stack). Documented so the backend exposes the right contracts.

### Stack
Next.js 16 (App Router, RSC, Server Actions), React 19, TypeScript, Tailwind +
shadcn/ui, TanStack Query, Zustand, Vercel AI SDK (generative UI + streaming),
Recharts/Tremor/D3, React Flow (agent/graph viz), SSE/WebSocket streaming,
Auth.js/Better-Auth, Docker/K8s/Vercel.

### Generative UI architecture
Backend agents emit **typed UI schemas** (`{type, component, data}`); the frontend
resolves them through a **Widget Registry** (Chart/Table/Research/Citation/
Timeline/Graph/Workflow/Agent/Evaluation/RetrievalTrace widgets). Widgets stream,
compose, and nest. This mirrors the backend registry pattern — every backend
capability becomes a renderable, streamable component.

### Layout & features
Three-panel workspace: left nav (Chats/Agents/Knowledge/Memory/Experiments/
Evaluations/Settings), center chat/canvas, right context panel (sources, traces,
metrics, **memory timeline**). Real-time agent graph (React Flow) over the
LangGraph trajectory; retrieval-trace inspector; no-code RAG config center;
experiment playground (model/architecture A/B with RAGAS + cost + latency);
observability dashboards (LangSmith/LangFuse); GraphRAG + memory-graph viz; Deep
Research mode; multimodal upload/preview.

### Contracts the backend must expose (incremental)
- Streaming chat with typed UI-schema events (SSE) over the existing pipelines.
- Session + memory APIs (this branch starts these).
- Experiment/eval read APIs (exist: `/experiments`, `/dashboard`).
- Trace APIs surfacing `RAGResult.trajectory` + retrieval traces.

### Scalability / security (target: 100k users, 100M docs, 1000+ agents)
Stateless API behind a gateway; pipelines/agents as horizontally-scaled workers;
Qdrant sharded/replicated; SQLite→Postgres for memory at scale (interface keeps
this swappable); Redis for working-memory cache + rate limiting; durable workflow
memory enables checkpoint/resume of long agents; per-tenant isolation, RBAC,
audit logs, encryption, PII controls; cost-aware model routing; backpressure on
streaming. The memory interfaces are storage-agnostic so SQLite→Postgres/Redis is
a backend swap, not a rewrite.

### Brutal-review risks (and mitigations)
- **Memory as silent context-bloat / prompt injection** → importance + dedup gate
  on formation, scope isolation, recall budget caps.
- **Vector/SQLite drift** → SQLite authoritative, Qdrant rebuildable projection.
- **Multi-tenant leakage** → scope filter enforced in every query, tested.
- **Long-agent restarts** → workflow memory checkpoints.
- **Unbounded growth/cost** → TTL + decay + prune + consolidation.
- **Streaming/state in FE** → server-authoritative state, idempotent events,
  resumable streams (frontend phase).
```
