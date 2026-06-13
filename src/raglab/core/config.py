"""Typed configuration + the composition root.

A YAML experiment file is parsed into :class:`ExperimentConfig`, then
``build_components``/``build_pipeline`` resolve each section into instantiated,
wired components via the registry. Swapping any component is a YAML edit only.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from raglab.core import registry
from raglab.core.interfaces import LLM, Embedder, Reranker, Retriever, VectorStore

# Embeddings can only come from these; OpenRouter (chat-only) is rejected here.
_EMBEDDING_NAMES = {"hashing", "openai", "cohere", "gemini", "bge_local", "e5_local"}


class EmbeddingCfg(BaseModel):
    name: str = "hashing"
    model: str | None = None
    dim: int | None = None
    options: dict[str, Any] = Field(default_factory=dict)


class ChunkerCfg(BaseModel):
    name: str = "recursive"  # recursive | fixed | parent_child
    chunk_size: int = 800
    overlap: int = 120
    options: dict[str, Any] = Field(default_factory=dict)


class VectorStoreCfg(BaseModel):
    name: str = "qdrant"
    url: str | None = None
    location: str | None = None  # e.g. ":memory:"
    distance: str = "cosine"


class RetrievalCfg(BaseModel):
    type: str = "dense"  # dense | bm25 | hybrid | multi_query
    k: int = 5
    dense_k: int = 20
    bm25_k: int = 20
    fusion: str = "rrf"  # rrf | mmr
    rrf_k: int = 60
    mmr_lambda: float = 0.5
    n_queries: int = 3  # for multi_query
    options: dict[str, Any] = Field(default_factory=dict)  # e.g. {mode: binary|int8}


class RerankerCfg(BaseModel):
    name: str = "noop"  # noop | cross_encoder | cohere
    model: str | None = None
    top_n: int = 5


class LLMCfg(BaseModel):
    provider: str = "echo"  # echo | openai | openrouter
    model: str | None = None
    temperature: float = 0.0
    max_tokens: int = 512


class AgentCfg(BaseModel):
    max_retrieval_retries: int = 2
    grade_threshold: float = 0.6
    enable_critic: bool = True


class GraphCfg(BaseModel):
    backend: str = "networkx"  # networkx | neo4j
    hops: int = 2
    extractor: str = "heuristic"  # heuristic | llm


class ObservabilityCfg(BaseModel):
    langfuse: bool = False
    langsmith: bool = False


class EvaluationCfg(BaseModel):
    ragas: bool = False
    judges: list[str] = Field(default_factory=list)
    builtin_metrics: list[str] = Field(
        default_factory=lambda: [
            "context_recall_proxy",
            "answer_relevancy_proxy",
            "answer_nonempty",
        ]
    )


class ExperimentConfig(BaseModel):
    collection: str = "raglab"
    architecture: str = "naive_rag"
    chunker: ChunkerCfg = Field(default_factory=ChunkerCfg)
    embedding: EmbeddingCfg = Field(default_factory=EmbeddingCfg)
    vectorstore: VectorStoreCfg = Field(default_factory=VectorStoreCfg)
    retrieval: RetrievalCfg = Field(default_factory=RetrievalCfg)
    reranker: RerankerCfg = Field(default_factory=RerankerCfg)
    llm: LLMCfg = Field(default_factory=LLMCfg)
    agent: AgentCfg = Field(default_factory=AgentCfg)
    graph: GraphCfg = Field(default_factory=GraphCfg)
    observability: ObservabilityCfg = Field(default_factory=ObservabilityCfg)
    evaluation: EvaluationCfg = Field(default_factory=EvaluationCfg)

    def model_post_init(self, _ctx: Any) -> None:
        if self.embedding.name not in _EMBEDDING_NAMES:
            raise ValueError(
                f"embedding.name {self.embedding.name!r} is not a valid embedder. "
                f"OpenRouter is chat-only; embeddings must be one of {sorted(_EMBEDDING_NAMES)}."
            )


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #
def load_config(path: str | Path) -> ExperimentConfig:
    data = yaml.safe_load(Path(path).read_text()) or {}
    return ExperimentConfig.model_validate(data)


def config_from_dict(data: dict[str, Any]) -> ExperimentConfig:
    return ExperimentConfig.model_validate(data)


# --------------------------------------------------------------------------- #
# Builders (composition root)
# --------------------------------------------------------------------------- #
@dataclass
class Components:
    """Resolved, wired components ready to hand to a pipeline."""

    config: ExperimentConfig
    embedder: Embedder
    store: VectorStore
    retriever: Retriever
    reranker: Reranker
    llm: LLM


def build_chunker(cfg: ChunkerCfg) -> Any:
    return registry.create(
        "chunker",
        cfg.name,
        chunk_size=cfg.chunk_size,
        overlap=cfg.overlap,
        **cfg.options,
    )


def build_embedder(cfg: EmbeddingCfg) -> Embedder:
    return registry.create(
        "embedder", cfg.name, model=cfg.model, dim=cfg.dim, **cfg.options
    )


def build_vectorstore(cfg: VectorStoreCfg, collection: str, dim: int) -> VectorStore:
    store: VectorStore = registry.create(
        "vectorstore",
        cfg.name,
        collection=collection,
        url=cfg.url,
        location=cfg.location,
        distance=cfg.distance,
    )
    store.ensure_collection(dim)
    return store


def build_retriever(
    cfg: RetrievalCfg, embedder: Embedder, store: VectorStore
) -> Retriever:
    if cfg.type == "dense":
        return registry.create("retriever", "dense", embedder=embedder, store=store)
    if cfg.type == "bm25":
        return registry.create("retriever", "bm25", store=store)
    if cfg.type == "compressed":
        return registry.create(
            "retriever",
            "compressed",
            embedder=embedder,
            store=store,
            mode=cfg.options.get("mode", "binary"),
        )
    if cfg.type == "hybrid":
        dense = registry.create("retriever", "dense", embedder=embedder, store=store)
        bm25 = registry.create("retriever", "bm25", store=store)
        return registry.create(
            "retriever",
            "hybrid",
            dense=dense,
            bm25=bm25,
            dense_k=cfg.dense_k,
            bm25_k=cfg.bm25_k,
            fusion=cfg.fusion,
            rrf_k=cfg.rrf_k,
            mmr_lambda=cfg.mmr_lambda,
            embedder=embedder,
        )
    if cfg.type == "multi_query":
        base = build_retriever(
            RetrievalCfg(type="hybrid", **cfg.model_dump(exclude={"type"})),
            embedder,
            store,
        )
        return registry.create(
            "retriever", "multi_query", base=base, n_queries=cfg.n_queries
        )
    raise ValueError(f"Unknown retrieval.type {cfg.type!r}")


def build_reranker(cfg: RerankerCfg) -> Reranker:
    return registry.create("reranker", cfg.name, model=cfg.model)


def build_llm(cfg: LLMCfg) -> LLM:
    return registry.create(
        "llm",
        cfg.provider,
        model=cfg.model,
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens,
    )


def build_components(config: ExperimentConfig) -> Components:
    embedder = build_embedder(config.embedding)
    store = build_vectorstore(config.vectorstore, config.collection, embedder.dim)
    retriever = build_retriever(config.retrieval, embedder, store)
    reranker = build_reranker(config.reranker)
    llm = build_llm(config.llm)
    return Components(
        config=config,
        embedder=embedder,
        store=store,
        retriever=retriever,
        reranker=reranker,
        llm=llm,
    )


def build_pipeline_from_components(config: ExperimentConfig, components: Components) -> Any:
    """Build the architecture pipeline around an already-resolved component set.

    Lets the caller (e.g. the benchmark runner / CLI) ingest into the same store
    the pipeline will query — essential for in-memory Qdrant where each client is
    isolated.
    """

    return registry.create("architecture", config.architecture, components=components)


def build_pipeline(config: ExperimentConfig) -> Any:
    """Resolve the full architecture pipeline from config."""

    return build_pipeline_from_components(config, build_components(config))
