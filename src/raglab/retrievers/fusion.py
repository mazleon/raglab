"""Rank/score fusion primitives shared by the hybrid retriever."""

from __future__ import annotations

import numpy as np

from raglab.core.types import ScoredChunk


def reciprocal_rank_fusion(
    result_lists: list[list[ScoredChunk]], rrf_k: int = 60
) -> list[ScoredChunk]:
    """Reciprocal Rank Fusion: score = sum 1/(rrf_k + rank) across lists.

    Deterministic and score-scale independent — the standard way to merge dense
    and sparse result lists.
    """

    scores: dict[str, float] = {}
    chunks: dict[str, ScoredChunk] = {}
    for results in result_lists:
        for rank, sc in enumerate(results):
            cid = sc.chunk.chunk_id or sc.chunk.text
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (rrf_k + rank + 1)
            chunks.setdefault(cid, sc)
    fused = [ScoredChunk(chunks[cid].chunk, score) for cid, score in scores.items()]
    fused.sort(key=lambda s: s.score, reverse=True)
    return fused


def mmr(
    query_vec: list[float],
    candidates: list[ScoredChunk],
    candidate_vecs: list[list[float]],
    k: int,
    lambda_mult: float = 0.5,
) -> list[ScoredChunk]:
    """Maximal Marginal Relevance: balance query relevance and diversity."""

    if not candidates:
        return []
    q = np.asarray(query_vec, dtype=np.float32)
    mat = np.asarray(candidate_vecs, dtype=np.float32)

    def _cos(a: np.ndarray, b: np.ndarray) -> np.ndarray:
        an = a / (np.linalg.norm(a) + 1e-9)
        bn = b / (np.linalg.norm(b, axis=-1, keepdims=True) + 1e-9)
        return bn @ an

    rel = _cos(q, mat)
    selected: list[int] = []
    remaining = list(range(len(candidates)))
    while remaining and len(selected) < k:
        if not selected:
            best = int(remaining[int(np.argmax(rel[remaining]))])
        else:
            best, best_score = remaining[0], -1e9
            for i in remaining:
                div = max(
                    float(_cos(mat[i], mat[selected].reshape(len(selected), -1)).max()),
                    0.0,
                )
                score = lambda_mult * float(rel[i]) - (1 - lambda_mult) * div
                if score > best_score:
                    best, best_score = i, score
        selected.append(best)
        remaining.remove(best)
    return [ScoredChunk(candidates[i].chunk, float(rel[i])) for i in selected]
