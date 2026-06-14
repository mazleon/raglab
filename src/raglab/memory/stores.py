"""The ten memory types.

Each is a registered, independently-replaceable ``MemoryStore``. Most are thin
specializations of :class:`BaseMemoryStore` (differing only in ``type`` and
whether they keep a semantic vector projection); a few add domain helpers
(episodes, preferences, workflow checkpoints, graph traversal).
"""

from __future__ import annotations

from typing import Any

from raglab.core.registry import register
from raglab.memory.base import BaseMemoryStore
from raglab.memory.scoring import importance_from_signals
from raglab.memory.types import (
    Episode,
    MemoryQuery,
    MemoryRecord,
    MemoryScope,
    WorkflowState,
)


@register("memory", "working")
class WorkingMemory(BaseMemoryStore):
    """Active session context: task state, plan, tool outputs. Short-lived."""

    type = "working"
    semantic = False

    def summarize(self, scope: MemoryScope, max_items: int = 20) -> str:
        items = self.sqlite.query(scope, types=[self.type], limit=max_items)
        return "\n".join(f"- {r.content}" for r in reversed(items))


@register("memory", "episodic")
class EpisodicMemory(BaseMemoryStore):
    """Past experiences (goal/action/result/feedback) for recall + learning."""

    type = "episodic"
    semantic = True

    def record_episode(self, episode: Episode, scope: MemoryScope) -> str:
        imp = importance_from_signals(
            episode.summary(), success=episode.success, has_feedback=bool(episode.feedback)
        )
        rec = MemoryRecord(
            content=episode.summary(), type=self.type, scope=scope,
            importance=imp, structured=episode.to_dict(),
        )
        return self.add(rec)


@register("memory", "semantic")
class SemanticMemory(BaseMemoryStore):
    """Facts and knowledge, retrieved by similarity + filter."""

    type = "semantic"
    semantic = True


@register("memory", "procedural")
class ProceduralMemory(BaseMemoryStore):
    """Workflows / playbooks / SOPs — how to perform tasks."""

    type = "procedural"
    semantic = True

    def save_playbook(self, name: str, steps: list[str], scope: MemoryScope) -> str:
        content = f"{name}\n" + "\n".join(f"{i + 1}. {s}" for i, s in enumerate(steps))
        rec = MemoryRecord(
            content=content, type=self.type, scope=scope, importance=0.7,
            structured={"name": name, "steps": steps},
        )
        return self.add(rec)


@register("memory", "long_term")
class LongTermMemory(BaseMemoryStore):
    """Durable preferences (user/project/org/agent). Survives sessions."""

    type = "long_term"
    semantic = False

    def set_pref(self, key: str, value: Any, scope: MemoryScope) -> str:
        # one record per (scope, key): replace existing
        for rec in self.sqlite.query(scope, types=[self.type], limit=500):
            if rec.structured.get("key") == key:
                self.delete(rec.id)
        rec = MemoryRecord(
            content=f"{key} = {value}", type=self.type, scope=scope, importance=0.9,
            structured={"key": key, "value": value},
        )
        return self.add(rec)

    def get_pref(self, key: str, scope: MemoryScope) -> Any | None:
        for rec in self.sqlite.query(scope, types=[self.type], limit=500):
            if rec.structured.get("key") == key:
                return rec.structured.get("value")
        return None


@register("memory", "reflection")
class ReflectionMemory(BaseMemoryStore):
    """What worked / failed / lessons — used by Self-RAG and critic agents."""

    type = "reflection"
    semantic = True


@register("memory", "agent")
class AgentMemory(BaseMemoryStore):
    """Per-agent private memory + success/failure history (scope.agent_id)."""

    type = "agent"
    semantic = True


@register("memory", "shared")
class SharedMemory(BaseMemoryStore):
    """Team memory accessible across agents in a tenant/session."""

    type = "shared"
    semantic = True


@register("memory", "workflow")
class WorkflowMemory(BaseMemoryStore):
    """Long-running workflow state with checkpoint + resume."""

    type = "workflow"
    semantic = False

    def save_state(
        self, state: WorkflowState, scope: MemoryScope, workflow_id: str | None = None
    ) -> str:
        rec = MemoryRecord(
            content=f"Workflow: {state.goal} [{state.status}] step {state.current_step}",
            type=self.type, scope=scope, importance=0.8, structured=state.to_dict(),
        )
        if workflow_id:
            rec.id = workflow_id
        return self.add(rec)

    def load_state(self, workflow_id: str) -> WorkflowState | None:
        rec = self.get(workflow_id)
        if rec is None:
            return None
        s = rec.structured
        return WorkflowState(
            goal=s.get("goal", ""), subtasks=s.get("subtasks", []),
            status=s.get("status", "running"), current_step=s.get("current_step", 0),
        )

    def checkpoint(self, workflow_id: str, state: WorkflowState, scope: MemoryScope) -> str:
        return self.save_state(state, scope, workflow_id=workflow_id)


@register("memory", "graph")
class GraphMemory(BaseMemoryStore):
    """Entity/relationship memory with multi-hop traversal.

    Relations are stored as records (structured subject/predicate/object) in
    SQLite and projected into Qdrant for content recall; traversal builds a
    networkx graph on demand from the records in scope.
    """

    type = "graph"
    semantic = True

    def add_relation(
        self, subject: str, predicate: str, obj: str, scope: MemoryScope
    ) -> str:
        rec = MemoryRecord(
            content=f"{subject} {predicate} {obj}", type=self.type, scope=scope,
            importance=0.6, structured={"subject": subject, "predicate": predicate, "object": obj},
        )
        return self.add(rec)

    def _graph(self, scope: MemoryScope):
        import networkx as nx

        g = nx.DiGraph()
        for rec in self.sqlite.query(scope, types=[self.type], limit=5000):
            s = rec.structured
            if s.get("subject") and s.get("object"):
                g.add_edge(s["subject"], s["object"], predicate=s.get("predicate", ""))
        return g

    def neighbors(self, entity: str, scope: MemoryScope) -> list[str]:
        g = self._graph(scope)
        if entity not in g:
            return []
        return sorted(set(g.successors(entity)) | set(g.predecessors(entity)))

    def traverse(self, entity: str, hops: int, scope: MemoryScope) -> list[str]:
        g = self._graph(scope).to_undirected()
        if entity not in g:
            return []
        import networkx as nx

        reached = nx.single_source_shortest_path_length(g, entity, cutoff=max(hops, 1))
        return sorted(n for n in reached if n != entity)


def query(text: str = "", scope: MemoryScope | None = None, **kw: Any) -> MemoryQuery:
    """Small convenience constructor used by callers/tests."""

    return MemoryQuery(text=text, scope=scope or MemoryScope(), **kw)
