# Embeddings, Reranking, and Evaluation

## Embeddings

RAGLab treats the embedding model as a swappable component. Supported providers
include OpenAI (text-embedding-3-large), Cohere (embed-english-v3.0), and local
BGE/E5 models via sentence-transformers. An offline hashing embedder is used by
default so the platform runs with no API keys.

## Vector store

Qdrant is the default vector database. It can run in-memory for tests or as a
Docker service for persistence. Vectors are stored with metadata including the
source, page, section, document id, and chunk id.

## Evaluation

RAGLab evaluates answers with RAGAS metrics — faithfulness, context precision,
context recall, answer relevancy, and answer correctness — plus configurable
LLM-as-judge graders. When no judge model is available, lightweight built-in
proxy metrics measure context recall and answer relevancy from token overlap so
the leaderboard still works offline.

## Cost and latency

Every run records latency in milliseconds, prompt and completion tokens, and an
estimated dollar cost computed from a per-model price table. These are reported
in the benchmark leaderboard alongside quality metrics.
