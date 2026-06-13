import pytest

from raglab.core.config import (
    ExperimentConfig,
    build_components,
    config_from_dict,
    load_config,
)


@pytest.mark.parametrize(
    "path",
    ["configs/naive.yaml", "configs/hybrid.yaml", "configs/agentic.yaml", "configs/ingest.yaml"],
)
def test_configs_load(path):
    cfg = load_config(path)
    assert isinstance(cfg, ExperimentConfig)


def test_openrouter_embedding_rejected():
    with pytest.raises(ValueError):
        config_from_dict({"embedding": {"name": "openrouter"}})


def test_build_components_offline_defaults():
    cfg = load_config("configs/hybrid.yaml")
    comps = build_components(cfg)
    assert comps.embedder.dim == 384
    # hybrid retriever wires dense + bm25
    assert comps.retriever.__class__.__name__ == "HybridRetriever"
