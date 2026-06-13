"""Agentic RAG — a LangGraph self-correcting retrieval/generation loop.

Graph:
    plan -> retrieve -> grade -> (rewrite -> retrieve)* -> generate -> critic
         -> (regenerate)? -> cite -> END

The grader scores retrieval quality; a low score triggers a bounded query-rewrite
+ retry loop. The critic checks the generated answer is grounded and can request
one regeneration before the citation step finalises the answer.
"""

from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, StateGraph

from raglab.agents import (
    attach_citations,
    critique_answer,
    grade_retrieval,
    rewrite_query,
)
from raglab.core.registry import register
from raglab.core.types import RAGResult, RunMetrics, ScoredChunk, TrajectoryStep, timer
from raglab.pipelines.base import BasePipeline, build_messages


class AgentState(TypedDict):
    query: str
    working_query: str
    contexts: list[ScoredChunk]
    answer: str
    retries: int
    regen: int
    grade: float
    critic_action: str
    trajectory: list[TrajectoryStep]
    metrics: RunMetrics


@register("architecture", "agentic_rag")
class AgenticRAG(BasePipeline):
    name = "agentic_rag"

    def __init__(self, components) -> None:  # type: ignore[no-untyped-def]
        super().__init__(components)
        self._app = self._build_graph()

    # --- nodes ---
    def _plan(self, state: AgentState) -> AgentState:
        state["working_query"] = state["query"]
        state["trajectory"].append(TrajectoryStep("plan", "drafted retrieval strategy"))
        return state

    def _retrieve(self, state: AgentState) -> AgentState:
        cfg = self.c.config
        candidates = self.c.retriever.retrieve(state["working_query"], cfg.retrieval.k)
        contexts = self.c.reranker.rerank(
            state["working_query"], candidates, cfg.reranker.top_n
        )
        state["contexts"] = contexts
        state["metrics"].retriever_hits = len(contexts)
        state["trajectory"].append(
            TrajectoryStep("retrieve", f"{len(contexts)} chunks", {"q": state["working_query"]})
        )
        return state

    def _grade(self, state: AgentState) -> AgentState:
        result = grade_retrieval(state["query"], state["contexts"])
        state["grade"] = result.score
        state["trajectory"].append(
            TrajectoryStep("grade", f"score={result.score} ({result.reason})")
        )
        return state

    def _rewrite(self, state: AgentState) -> AgentState:
        state["retries"] += 1
        state["metrics"].retries = state["retries"]
        state["working_query"] = rewrite_query(state["query"], state["retries"])
        state["trajectory"].append(
            TrajectoryStep("rewrite", state["working_query"])
        )
        return state

    def _generate(self, state: AgentState) -> AgentState:  # type: ignore[override]
        resp = self.c.llm.generate(build_messages(state["query"], state["contexts"]))
        state["metrics"].add_llm(resp)
        state["answer"] = resp.text
        state["trajectory"].append(TrajectoryStep("generate", resp.model))
        return state

    def _critic(self, state: AgentState) -> AgentState:
        if not self.c.config.agent.enable_critic:
            state["critic_action"] = "cite"
            return state
        result = critique_answer(state["query"], state["answer"], state["contexts"])
        if not result.ok and state["regen"] < 1:
            state["regen"] += 1
            state["critic_action"] = "regenerate"
        else:
            state["critic_action"] = "cite"
        state["trajectory"].append(
            TrajectoryStep("critic", f"{result.reason} -> {state['critic_action']}")
        )
        return state

    def _cite(self, state: AgentState) -> AgentState:
        answer, sources = attach_citations(state["answer"], state["contexts"])
        state["answer"] = answer
        state["trajectory"].append(
            TrajectoryStep("cite", f"{len(sources)} sources", {"sources": sources})
        )
        return state

    # --- routing ---
    def _after_grade(self, state: AgentState) -> str:
        cfg = self.c.config.agent
        if state["grade"] >= cfg.grade_threshold or state["retries"] >= cfg.max_retrieval_retries:
            return "generate"
        return "rewrite"

    def _after_critic(self, state: AgentState) -> str:
        return state["critic_action"]

    def _build_graph(self):
        g = StateGraph(AgentState)
        g.add_node("plan", self._plan)
        g.add_node("retrieve", self._retrieve)
        g.add_node("grade", self._grade)
        g.add_node("rewrite", self._rewrite)
        g.add_node("generate", self._generate)
        g.add_node("critic", self._critic)
        g.add_node("cite", self._cite)

        g.set_entry_point("plan")
        g.add_edge("plan", "retrieve")
        g.add_edge("retrieve", "grade")
        g.add_conditional_edges(
            "grade", self._after_grade, {"generate": "generate", "rewrite": "rewrite"}
        )
        g.add_edge("rewrite", "retrieve")
        g.add_edge("generate", "critic")
        g.add_conditional_edges(
            "critic", self._after_critic, {"regenerate": "generate", "cite": "cite"}
        )
        g.add_edge("cite", END)
        return g.compile()

    # --- entrypoint ---
    def run(self, query: str) -> RAGResult:
        metrics = RunMetrics()
        init: AgentState = {
            "query": query,
            "working_query": query,
            "contexts": [],
            "answer": "",
            "retries": 0,
            "regen": 0,
            "grade": 0.0,
            "critic_action": "cite",
            "trajectory": [],
            "metrics": metrics,
        }
        with timer(metrics):
            final = self._app.invoke(init)
        return RAGResult(
            query=query,
            answer=final["answer"],
            contexts=final["contexts"],
            trajectory=final["trajectory"],
            metrics=metrics,
            architecture=self.name,
        )
