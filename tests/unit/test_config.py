import pytest

from raglab.core.config import (
    ExperimentConfig,
    build_components,
    config_from_dict,
    load_config,
)


@pytest.mark.parametrize(
    "path",
    [
        "configs/pipelines/naive.yaml",
        "configs/pipelines/hybrid.yaml",
        "configs/pipelines/agentic.yaml",
        "configs/pipelines/cloud.yaml",
        "configs/ingest.yaml",
    ],
)
def test_configs_load(path):
    cfg = load_config(path)
    assert isinstance(cfg, ExperimentConfig)


def test_openrouter_embedding_rejected():
    from raglab.errors import ConfigError

    with pytest.raises(ConfigError):
        config_from_dict({"embedding": {"name": "openrouter"}})


def test_build_components_offline_defaults():
    cfg = load_config("configs/pipelines/hybrid.yaml")
    comps = build_components(cfg)
    assert comps.embedder.dim == 384
    # hybrid retriever wires dense + bm25
    assert comps.retriever.__class__.__name__ == "HybridRetriever"
