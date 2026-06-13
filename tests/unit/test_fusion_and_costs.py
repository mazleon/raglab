from raglab.core.types import Chunk, ScoredChunk
from raglab.llms.costs import cost_usd
from raglab.retrievers.fusion import reciprocal_rank_fusion


def _sc(cid: str, score: float = 0.0) -> ScoredChunk:
    return ScoredChunk(Chunk(text=cid, chunk_id=cid), score)


def test_rrf_rewards_agreement_across_lists():
    list_a = [_sc("x"), _sc("y"), _sc("z")]
    list_b = [_sc("y"), _sc("x"), _sc("w")]
    fused = reciprocal_rank_fusion([list_a, list_b], rrf_k=60)
    # x is rank0+rank1, y is rank1+rank0 -> both beat singletons z, w
    top_ids = [s.chunk.chunk_id for s in fused[:2]]
    assert set(top_ids) == {"x", "y"}
    assert fused[0].score == fused[1].score  # symmetric


def test_rrf_score_formula():
    fused = reciprocal_rank_fusion([[_sc("a")]], rrf_k=60)
    assert abs(fused[0].score - 1.0 / 61) < 1e-9


def test_cost_table():
    assert cost_usd("gpt-4o-mini", 1000, 1000) > 0
    assert cost_usd("unknown-model", 1000, 1000) == 0.0
