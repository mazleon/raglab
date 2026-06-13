from raglab.core import registry


def test_bootstrap_registers_core_components():
    assert "hashing" in registry.available("embedder")
    assert "qdrant" in registry.available("vectorstore")
    assert set(registry.available("retriever")) >= {"dense", "bm25", "hybrid"}
    assert "noop" in registry.available("reranker")
    assert "echo" in registry.available("llm")


def test_all_architectures_registered():
    arch = registry.available("architecture")
    assert {"naive_rag", "hybrid_rag", "agentic_rag"} <= set(arch)
    # 3 implemented + 10 planned stubs
    assert len(arch) >= 13


def test_unknown_component_raises_with_options():
    try:
        registry.get("embedder", "does-not-exist")
    except KeyError as e:
        assert "Available" in str(e)
    else:  # pragma: no cover
        raise AssertionError("expected KeyError")
