"""Unit tests for Phase 2 (GraphRAG), Phase 4 (chunkers), Phase 6 (compressed)."""

from raglab.agents.reasoning import classify_complexity, decompose, identify_gaps
from raglab.core.config import build_embedder, build_vectorstore, load_config
from raglab.core.registry import create
from raglab.core.types import Chunk, Document, ScoredChunk
from raglab.experiments.store import list_experiments, save_experiments
from raglab.graph.store import NetworkXGraphStore
from raglab.ingestion.pipeline import IngestionPipeline


def test_graph_store_builds_and_traverses():
    g = NetworkXGraphStore()
    g.build_from_chunks(
        [
            Chunk("Qdrant stores vectors for RAGLab retrieval.", {}, "c1", "d1"),
            Chunk("Cohere reranks documents in RAGLab.", {}, "c2", "d1"),
        ]
    )
    assert g.num_entities > 0
    assert g.num_relations >= 0
    hits = g.entity_search("Qdrant", 5)
    assert any("Qdrant" in h.text for h in hits)
    assert isinstance(g.communities(), list)


def test_reasoning_helpers():
    assert classify_complexity("hi") == "simple"
    assert classify_complexity("Compare A and B and C in detail across systems") == "complex"
    subs = decompose("What is RRF and how does Qdrant store vectors?")
    assert len(subs) >= 2
    gaps = identify_gaps("quantum chromodynamics", [ScoredChunk(Chunk("cats and dogs"))])
    assert "quantum" in gaps or "chromodynamics" in gaps


def test_semantic_and_agentic_chunkers():
    doc = Document(text="RAGLab benchmarks RAG. Qdrant stores vectors. RRF merges lists.",
                   metadata={"source": "t"})
    for name in ("semantic", "agentic"):
        chunks = create("chunker", name).chunk([doc])
        assert chunks and all(c.text for c in chunks)


def test_compressed_retriever_modes():
    cfg = load_config("configs/naive.yaml")
    emb = build_embedder(cfg.embedding)
    store = build_vectorstore(cfg.vectorstore, "comp_unit", emb.dim)
    IngestionPipeline(create("chunker", "recursive"), emb, store).ingest("examples/docs")
    for mode in ("binary", "int8"):
        r = create("retriever", "compressed", embedder=emb, store=store, mode=mode)
        hits = r.retrieve("How does RRF score documents?", 3)
        assert len(hits) == 3
        assert r.compression_ratio in (4.0, 32.0)


def test_experiment_store_roundtrip(tmp_path):
    db = tmp_path / "exp.db"
    rows = [
        {
            "experiment_id": "abc123",
            "architecture": "naive_rag",
            "embedding": "hashing",
            "retrieval": "dense",
            "reranker": "noop",
            "llm": "echo",
            "n_questions": 5,
            "context_recall_proxy": 0.9,
            "avg_latency_ms": 1.0,
            "total_cost_usd": 0.0,
            "avg_tokens": 100.0,
            "timestamp": "2026-06-13T00:00:00+00:00",
        }
    ]
    assert save_experiments(rows, db) == 1
    out = list_experiments(db)
    assert len(out) == 1
    assert out[0]["architecture"] == "naive_rag"
    assert out[0]["context_recall_proxy"] == 0.9  # restored from metrics_json
