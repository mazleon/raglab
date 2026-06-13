# RAGLab Overview

RAGLab is a modular platform for benchmarking Retrieval-Augmented Generation
(RAG) systems. It lets researchers run the same query across many architectures
and compare retrieval quality, faithfulness, latency, and cost under identical
conditions.

## Architectures

RAGLab supports Naive RAG, Hybrid RAG, and Agentic RAG today, with stubs for
Corrective RAG (CRAG), Self-RAG, Adaptive RAG, GraphRAG, Multi-Hop RAG, and
others. Every architecture implements the same `Pipeline` interface, so the
benchmark runner can drive them all without special-casing.

## Hybrid retrieval

Hybrid retrieval combines dense vector search with sparse BM25 keyword search.
The two result lists are merged with Reciprocal Rank Fusion (RRF), which scores
each document by the sum of 1 / (k + rank) across the lists it appears in. A
reranker such as a cross-encoder or Cohere Rerank can then reorder the fused
candidates before generation.

## Agentic RAG

Agentic RAG adds a self-correcting loop. A planner drafts a retrieval strategy,
a grader scores whether the retrieved context is relevant and complete, and if
the score is low the agent rewrites the query and retries. A critic reviews the
generated answer before it is returned, and a citation step attaches sources.
