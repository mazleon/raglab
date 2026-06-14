"""Memory Engineering Platform tests (offline: SQLite + in-memory Qdrant + hashing)."""

import pytest

from raglab.memory import (
    MEMORY_TYPES,
    Episode,
    MemoryManager,
    MemoryQuery,
    MemoryScope,
    WorkflowState,
)
from raglab.memory.formation import MemoryFormationEngine
from raglab.memory.scoring import combined_score, importance_from_signals, recency_score
from raglab.memory.types import _now


@pytest.fixture
def manager():
    m = MemoryManager()
    yield m
    m.close()


SCOPE = MemoryScope(tenant_id="acme", user_id="leon", session_id="s1")


def test_all_ten_types_registered(manager):
    assert set(manager.stores) == set(MEMORY_TYPES)
    assert len(MEMORY_TYPES) == 10


def test_remember_and_recall_semantic(manager):
    manager.remember("semantic", "RRF scores documents by 1/(k+rank) across lists.", SCOPE)
    manager.remember("semantic", "Bananas are a yellow fruit.", SCOPE)
    hits = manager.recall(MemoryQuery(text="reciprocal rank fusion scoring", scope=SCOPE, k=2))
    assert hits
    assert "rrf" in hits[0].content.lower() or "rank" in hits[0].content.lower()
    assert hits[0].score >= hits[-1].score  # ranked


def test_formation_drops_low_importance(manager):
    # very short, low-importance content is forgotten by the formation gate
    mid = manager.remember("semantic", "ok", SCOPE, importance=0.1)
    assert mid is None
    forced = manager.remember("semantic", "ok", SCOPE, importance=0.1, force=True)
    assert forced is not None


def test_scope_isolation(manager):
    other = MemoryScope(tenant_id="other", user_id="x")
    manager.remember("semantic", "secret tenant data about RRF", SCOPE, force=True)
    hits = manager.recall(MemoryQuery(text="RRF", scope=other, k=5))
    assert hits == []  # different tenant sees nothing


def test_episodic_records_and_recalls(manager):
    manager.store("episodic").record_episode(
        Episode(goal="answer RRF", action="hybrid", result="ok", success=True), SCOPE
    )
    hits = manager.recall(MemoryQuery(text="RRF", scope=SCOPE, k=3), types=["episodic"])
    assert hits and hits[0].record.type == "episodic"


def test_long_term_prefs(manager):
    lt = manager.store("long_term")
    lt.set_pref("preferred_rag", "GraphRAG", SCOPE)
    assert lt.get_pref("preferred_rag", SCOPE) == "GraphRAG"
    lt.set_pref("preferred_rag", "Agentic", SCOPE)  # replace
    assert lt.get_pref("preferred_rag", SCOPE) == "Agentic"


def test_workflow_checkpoint_resume(manager):
    wf = manager.store("workflow")
    wid = wf.save_state(WorkflowState(goal="research", current_step=2, status="paused"), SCOPE)
    state = wf.load_state(wid)
    assert state.goal == "research" and state.current_step == 2 and state.status == "paused"


def test_graph_memory_traversal(manager):
    g = manager.store("graph")
    g.add_relation("Leon", "researches", "Agentic RAG", SCOPE)
    g.add_relation("Agentic RAG", "uses", "GraphRAG", SCOPE)
    assert "GraphRAG" in g.neighbors("Agentic RAG", SCOPE)
    assert set(g.traverse("Leon", 2, SCOPE)) == {"Agentic RAG", "GraphRAG"}


def test_ttl_expiry(manager):
    from datetime import timedelta

    from raglab.memory.types import now_dt

    mid = manager.remember("working", "ephemeral task note", SCOPE, ttl_seconds=60, force=True)
    # force it expired in the past
    past = (now_dt() - timedelta(hours=1)).isoformat()
    manager.sqlite.update(mid, expires_at=past)
    removed = manager.lifecycle.expire_ttl()
    assert removed >= 1
    assert manager.sqlite.get(mid) is None


def test_dedup(manager):
    manager.remember("semantic", "duplicate fact about Qdrant", SCOPE, force=True)
    manager.remember("semantic", "duplicate fact about Qdrant", SCOPE, force=True)
    deduped = manager.lifecycle.dedup(SCOPE)
    assert deduped == 1


def test_consolidate_and_stats(manager):
    manager.remember("working", "task: compare retrievers", SCOPE, force=True)
    manager.store("episodic").record_episode(
        Episode(goal="g", action="a", result="r", success=True), SCOPE
    )
    cid = manager.consolidate(SCOPE)
    assert cid is not None
    stats = manager.stats(SCOPE)
    assert stats["total"] >= 3
    assert "long_term" in stats["by_type"]


def test_gdpr_erase(manager):
    manager.remember("semantic", "personal note one", SCOPE, force=True)
    manager.remember("semantic", "personal note two", SCOPE, force=True)
    erased = manager.erase(MemoryScope(tenant_id="acme", user_id="leon"))
    assert erased >= 2
    assert manager.stats(SCOPE)["total"] == 0


def test_audit_log(manager):
    manager.remember("semantic", "auditable fact", SCOPE, force=True)
    log = manager.audit(SCOPE, limit=10)
    assert any(e["action"] == "create" for e in log)


def test_scoring_helpers():
    assert importance_from_signals("x", success=False) > importance_from_signals("x", success=True)
    assert 0.0 < recency_score(_now()) <= 1.0
    assert combined_score(1.0, 1.0, 1.0) == 1.0


def test_formation_engine():
    f = MemoryFormationEngine(importance_threshold=0.3)
    assert f.should_remember("important content here", 0.5)
    assert not f.should_remember("", 0.9)
    assert f.decide("x" * 5000, 0.9).action == "summarize"


@pytest.mark.integration
def test_agentic_loop_uses_memory(manager, tmp_path):
    """Opt-in episodic memory: the agentic loop recalls + records episodes."""

    from raglab.core.config import load_config
    from raglab.service import build_engine

    corpus = tmp_path / "c"
    corpus.mkdir()
    (corpus / "d.md").write_text(
        "Reciprocal Rank Fusion (RRF) scores each document by 1/(k+rank) across lists."
    )
    cfg = load_config("configs/pipelines/agentic.yaml")
    engine = build_engine(cfg, ingest_path=str(corpus))
    engine.pipeline.attach_memory(manager, SCOPE)  # type: ignore[attr-defined]

    result = engine.answer("How does Reciprocal Rank Fusion score documents?")
    assert any(s.name == "recall_memory" for s in result.trajectory)
    episodes = manager.store("episodic").list(SCOPE)
    assert len(episodes) >= 1  # an episode was recorded

