# Graph Report - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab  (2026-06-13)

## Corpus Check
- Corpus is ~11,558 words - fits in a single context window. You may not need a graph.

## Summary
- 618 nodes · 1342 edges · 33 communities detected
- Extraction: 61% EXTRACTED · 39% INFERRED · 0% AMBIGUOUS · INFERRED: 530 edges (avg confidence: 0.61)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Core Interfaces & Types|Core Interfaces & Types]]
- [[_COMMUNITY_RAG Pipelines|RAG Pipelines]]
- [[_COMMUNITY_Benchmarking & Evaluation|Benchmarking & Evaluation]]
- [[_COMMUNITY_Documentation & Architecture|Documentation & Architecture]]
- [[_COMMUNITY_Package Initializers|Package Initializers]]
- [[_COMMUNITY_API Service & Observability|API Service & Observability]]
- [[_COMMUNITY_Configuration & CLI|Configuration & CLI]]
- [[_COMMUNITY_Architecture Documentation|Architecture Documentation]]
- [[_COMMUNITY_Retrieval & Vector Store|Retrieval & Vector Store]]
- [[_COMMUNITY_Fusion & Multi-Query|Fusion & Multi-Query]]
- [[_COMMUNITY_CLI & Ingestion|CLI & Ingestion]]
- [[_COMMUNITY_LLM & Evaluation Judges|LLM & Evaluation Judges]]
- [[_COMMUNITY_OpenAI-Compatible LLMs & Costs|OpenAI-Compatible LLMs & Costs]]
- [[_COMMUNITY_Recursive Chunkers|Recursive Chunkers]]
- [[_COMMUNITY_Agent Critic & Grading|Agent Critic & Grading]]
- [[_COMMUNITY_Advanced RAG Roadmap|Advanced RAG Roadmap]]
- [[_COMMUNITY_Text Parsers|Text Parsers]]
- [[_COMMUNITY_Local Embeddings|Local Embeddings]]
- [[_COMMUNITY_Embedding Provider Roadmap|Embedding Provider Roadmap]]
- [[_COMMUNITY_Cohere Embeddings|Cohere Embeddings]]
- [[_COMMUNITY_Hashing Embedder|Hashing Embedder]]
- [[_COMMUNITY_PDF & DOCX Parsers|PDF & DOCX Parsers]]
- [[_COMMUNITY_OpenAI Embeddings|OpenAI Embeddings]]
- [[_COMMUNITY_Cohere Reranker|Cohere Reranker]]
- [[_COMMUNITY_Cross-Encoder Reranker|Cross-Encoder Reranker]]
- [[_COMMUNITY_Core Data Types|Core Data Types]]
- [[_COMMUNITY_GraphRAG Roadmap|GraphRAG Roadmap]]
- [[_COMMUNITY_Timer Utility|Timer Utility]]
- [[_COMMUNITY_Pipeline Stubs|Pipeline Stubs]]
- [[_COMMUNITY_Dashboard Roadmap|Dashboard Roadmap]]
- [[_COMMUNITY_Compression Roadmap|Compression Roadmap]]
- [[_COMMUNITY_Tracer Protocol|Tracer Protocol]]
- [[_COMMUNITY_CICD Roadmap|CI/CD Roadmap]]

## God Nodes (most connected - your core abstractions)
1. `ScoredChunk` - 62 edges
2. `Document` - 45 edges
3. `Chunk` - 40 edges
4. `get()` - 38 edges
5. `Evaluation: built-in proxy metrics, RAGAS, LLM judges, and reports.` - 35 edges
6. `VectorStore` - 35 edges
7. `RAGResult` - 35 edges
8. `Embedder` - 33 edges
9. `LLMResponse` - 33 edges
10. `Retriever` - 29 edges

## Surprising Connections (you probably didn't know these)
- `Hybrid RAG` --semantically_similar_to--> `Hybrid Retrieval`  [INFERRED] [semantically similar]
  README.md → examples/docs/raglab_overview.md
- `GraphRAG` --semantically_similar_to--> `Phase 2 GraphRAG`  [INFERRED] [semantically similar]
  examples/docs/raglab_overview.md → docs/ROADMAP.md
- `Modular Core` --semantically_similar_to--> `Design Principle`  [INFERRED] [semantically similar]
  README.md → docs/ARCHITECTURE.md
- `Naive RAG` --semantically_similar_to--> `Naive RAG`  [INFERRED] [semantically similar]
  README.md → examples/docs/raglab_overview.md
- `Hybrid RAG` --semantically_similar_to--> `Hybrid RAG`  [INFERRED] [semantically similar]
  README.md → examples/docs/raglab_overview.md

## Hyperedges (group relationships)
- **Hybrid Retrieval Flow** — overview_dense_search, overview_bm25_search, overview_rrf, overview_reranker [EXTRACTED 1.00]
- **Agentic RAG State Machine** — overview_planner, overview_grader, overview_query_rewriter, overview_critic, overview_citation_step [EXTRACTED 1.00]
- **RAGAS Metrics** — embeddings_eval_faithfulness, embeddings_eval_context_precision, embeddings_eval_context_recall, embeddings_eval_answer_relevancy, embeddings_eval_answer_correctness [EXTRACTED 1.00]

## Communities

### Community 0 - "Core Interfaces & Types"
Cohesion: 0.09
Nodes (53): Components, ExperimentConfig, Typed configuration + the composition root.  A YAML experiment file is parsed in, Resolved, wired components ready to hand to a pipeline., Build the architecture pipeline around an already-resolved component set.      L, Resolve the full architecture pipeline from config., DenseRetriever, Dense vector retriever — embeds the query and searches the vector store. (+45 more)

### Community 1 - "RAG Pipelines"
Cohesion: 0.07
Nodes (24): AgenticRAG, AgentState, Agentic RAG — a LangGraph self-correcting retrieval/generation loop.  Graph:, BasePipeline, build_messages(), format_context(), Shared pipeline plumbing: prompt formatting and grounded generation.  The prompt, Holds resolved components and a metrics accumulator helper. (+16 more)

### Community 2 - "Benchmarking & Evaluation"
Cohesion: 0.1
Nodes (32): answer_nonempty(), answer_relevancy_proxy(), context_recall_proxy(), _ctx_tokens(), evaluate_builtin(), faithfulness_proxy(), Built-in proxy metrics — LLM-free, deterministic, always available.  They approx, Mean of each requested metric across records. (+24 more)

### Community 3 - "Documentation & Architecture"
Cohesion: 0.06
Nodes (40): Benchmark Runner, Chunker Protocol, Embedder Protocol, Evaluator Protocol, Hybrid RAG Sequence, Ingestion Flow, LLM Protocol, Parser Protocol (+32 more)

### Community 4 - "Package Initializers"
Cohesion: 0.06
Nodes (6): clean_documents(), clean_text(), GraphStore, parse_path(), parser_for(), Evaluation: built-in proxy metrics, RAGAS, LLM judges, and reports.

### Community 5 - "API Service & Observability"
Cohesion: 0.1
Nodes (23): architectures(), benchmark(), BenchmarkRequest, health(), query(), QueryRequest, QueryResponse, FastAPI service exposing the same pipelines as the CLI.      uvicorn raglab.api: (+15 more)

### Community 6 - "Configuration & CLI"
Cohesion: 0.16
Nodes (28): BaseModel, ingest(), Parse, chunk, embed, and upsert documents into the vector store., AgentCfg, build_chunker(), build_components(), build_embedder(), build_llm() (+20 more)

### Community 7 - "Architecture Documentation"
Cohesion: 0.08
Nodes (32): Agentic RAG State Machine, core/config.py, core/interfaces.py, core/registry.py, Design Principle, Interfaces, Pipeline Protocol, Rationale: interface isolation (+24 more)

### Community 8 - "Retrieval & Vector Store"
Cohesion: 0.14
Nodes (6): BM25Retriever, Sparse BM25 keyword retriever over all chunks in the store.  Builds an in-memory, _tok(), _point_id(), QdrantStore, Qdrant vector store adapter.  Runs in-memory (``location: ":memory:"``) for test

### Community 9 - "Fusion & Multi-Query"
Cohesion: 0.15
Nodes (12): mmr(), Rank/score fusion primitives shared by the hybrid retriever., Reciprocal Rank Fusion: score = sum 1/(rrf_k + rank) across lists.      Determin, Maximal Marginal Relevance: balance query relevance and diversity., reciprocal_rank_fusion(), MultiQueryRetriever, Multi-query retriever: paraphrase the query into N variants, retrieve each, and, _variants() (+4 more)

### Community 10 - "CLI & Ingestion"
Cohesion: 0.15
Nodes (13): architectures(), bench(), components(), main(), query(), RAGLab command-line interface (Typer).      raglab ingest <path> --config config, List every registered architecture (implemented + planned stubs)., List every registered component by kind. (+5 more)

### Community 11 - "LLM & Evaluation Judges"
Cohesion: 0.19
Nodes (8): EchoLLM, _extract_context(), _extract_question(), model(), Offline extractive 'LLM'.  Produces deterministic answers by selecting the sente, _tokens(), LLMJudge, LLM-as-judge evaluators.  Each judge prompts a (configurable, swappable) LLM to

### Community 12 - "OpenAI-Compatible LLMs & Costs"
Cohesion: 0.23
Nodes (7): cost_usd(), Per-model price table (USD per 1K tokens) and cost computation.  Prices are appr, model(), _OpenAICompatLLM, OpenAILLM, OpenRouterLLM, OpenAI and OpenRouter chat adapters.  Both speak the OpenAI Chat Completions API

### Community 13 - "Recursive Chunkers"
Cohesion: 0.29
Nodes (6): _emit(), FixedChunker, _overlap(), Recursive + fixed + parent-child chunkers.  The recursive splitter mirrors LangC, RecursiveChunker, _split()

### Community 14 - "Agent Critic & Grading"
Cohesion: 0.27
Nodes (9): attach_citations(), critique_answer(), CritiqueResult, Answer critic + citation attachment., Flag ungrounded or empty answers. Heuristic: the answer must be non-empty     an, _content_tokens(), grade_retrieval(), GradeResult (+1 more)

### Community 15 - "Advanced RAG Roadmap"
Cohesion: 0.15
Nodes (13): Adaptive RAG, Corrective RAG (CRAG), Multi-Hop RAG, Self-RAG, adaptive_rag, advanced_rag, crag, deep_search_rag (+5 more)

### Community 16 - "Text Parsers"
Cohesion: 0.21
Nodes (4): CSVParser, HTMLParser, Plain-text / Markdown / HTML / CSV parsers (dependency-free)., TextParser

### Community 17 - "Local Embeddings"
Cohesion: 0.35
Nodes (5): BGEEmbedder, dim(), E5Embedder, Local sentence-transformers embedders (BGE / E5). Requires the ``local`` extra., _SentenceTransformerEmbedder

### Community 18 - "Embedding Provider Roadmap"
Cohesion: 0.18
Nodes (11): Agentic Chunker, BGE Reranker, Docling Parser, E5 Embeddings, Gemini Embeddings, Instructor Embeddings, LlamaParse Parser, Phase 4 More Providers (+3 more)

### Community 19 - "Cohere Embeddings"
Cohesion: 0.31
Nodes (3): CohereEmbedder, dim(), Cohere embeddings adapter (requires the ``providers`` extra + COHERE_API_KEY).

### Community 20 - "Hashing Embedder"
Cohesion: 0.33
Nodes (4): dim(), HashingEmbedder, Deterministic, dependency-free embedder.  Hashes tokens into a fixed-dimensional, _tokenize()

### Community 21 - "PDF & DOCX Parsers"
Cohesion: 0.28
Nodes (3): DocxParser, PDFParser, PDF and DOCX parsers (require the ``parsers`` extra).

### Community 22 - "OpenAI Embeddings"
Cohesion: 0.33
Nodes (3): dim(), OpenAIEmbedder, OpenAI embeddings adapter (requires the ``providers`` extra + OPENAI_API_KEY).

### Community 23 - "Cohere Reranker"
Cohesion: 0.38
Nodes (2): CohereReranker, Cohere Rerank adapter (requires the ``providers`` extra + COHERE_API_KEY).

### Community 24 - "Cross-Encoder Reranker"
Cohesion: 0.38
Nodes (2): CrossEncoderReranker, Local cross-encoder reranker (requires the ``local`` extra).

### Community 25 - "Core Data Types"
Cohesion: 0.33
Nodes (6): Chunk Type, Document Type, RAGResult Type, RunMetrics, ScoredChunk Type, Cost and Latency Tracking

### Community 26 - "GraphRAG Roadmap"
Cohesion: 0.33
Nodes (6): GraphRAG, Community Detection, Entity Extraction, Multi-hop Traversal, Neo4j GraphStore, Phase 2 GraphRAG

### Community 27 - "Timer Utility"
Cohesion: 0.4
Nodes (2): Context manager that records elapsed wall-clock time into RunMetrics., _Timer

### Community 28 - "Pipeline Stubs"
Cohesion: 0.67
Nodes (2): _make_stub(), Registered stubs for architectures planned in later phases.  They conform to the

### Community 29 - "Dashboard Roadmap"
Cohesion: 0.67
Nodes (3): Experiment Store, Phase 5 Experiment Dashboard, Web UI

### Community 30 - "Compression Roadmap"
Cohesion: 1.0
Nodes (2): Phase 6 Compressed Retrieval, TurboVec/TurboQuant

### Community 39 - "Tracer Protocol"
Cohesion: 1.0
Nodes (1): Tracer Protocol

### Community 40 - "CI/CD Roadmap"
Cohesion: 1.0
Nodes (1): CI/CD

## Knowledge Gaps
- **78 isolated node(s):** `Class decorator that records ``cls`` under ``(kind, name)``.`, `Import every implementation package so registrations run. Idempotent.`, `Instantiate a registered component.`, `A parsed source document, before chunking.`, `A retrievable unit of text with provenance metadata.      Metadata conventionall` (+73 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Cohere Reranker`** (7 nodes): `CohereReranker`, `._ensure()`, `.__init__()`, `.rerank()`, `Cohere Rerank adapter (requires the ``providers`` extra + COHERE_API_KEY).`, `cohere_rerank.py`, `cohere_rerank.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Cross-Encoder Reranker`** (7 nodes): `CrossEncoderReranker`, `._ensure()`, `.__init__()`, `.rerank()`, `Local cross-encoder reranker (requires the ``local`` extra).`, `cross_encoder.py`, `cross_encoder.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Timer Utility`** (5 nodes): `Context manager that records elapsed wall-clock time into RunMetrics.`, `_Timer`, `.__enter__()`, `.__exit__()`, `.__init__()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Pipeline Stubs`** (4 nodes): `stubs.py`, `_make_stub()`, `Registered stubs for architectures planned in later phases.  They conform to the`, `stubs.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Compression Roadmap`** (2 nodes): `Phase 6 Compressed Retrieval`, `TurboVec/TurboQuant`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Tracer Protocol`** (1 nodes): `Tracer Protocol`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `CI/CD Roadmap`** (1 nodes): `CI/CD`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ScoredChunk` connect `Core Interfaces & Types` to `RAG Pipelines`, `Package Initializers`, `Retrieval & Vector Store`, `Fusion & Multi-Query`, `Agent Critic & Grading`, `Cohere Reranker`, `Cross-Encoder Reranker`?**
  _High betweenness centrality (0.158) - this node is a cross-community bridge._
- **Why does `get()` connect `Benchmarking & Evaluation` to `Core Interfaces & Types`, `RAG Pipelines`, `API Service & Observability`, `Configuration & CLI`, `Retrieval & Vector Store`, `Fusion & Multi-Query`, `CLI & Ingestion`, `LLM & Evaluation Judges`, `OpenAI-Compatible LLMs & Costs`, `Agent Critic & Grading`, `Cohere Embeddings`, `OpenAI Embeddings`, `Cohere Reranker`?**
  _High betweenness centrality (0.149) - this node is a cross-community bridge._
- **Why does `Document` connect `Core Interfaces & Types` to `Text Parsers`, `Recursive Chunkers`, `Package Initializers`, `PDF & DOCX Parsers`?**
  _High betweenness centrality (0.085) - this node is a cross-community bridge._
- **Are the 59 inferred relationships involving `ScoredChunk` (e.g. with `BM25Retriever` and `Sparse BM25 keyword retriever over all chunks in the store.  Builds an in-memory`) actually correct?**
  _`ScoredChunk` has 59 INFERRED edges - model-reasoned connections that need verification._
- **Are the 42 inferred relationships involving `Document` (e.g. with `Evaluation: built-in proxy metrics, RAGAS, LLM judges, and reports.` and `Return the first registered parser that supports ``path``.`) actually correct?**
  _`Document` has 42 INFERRED edges - model-reasoned connections that need verification._
- **Are the 37 inferred relationships involving `Chunk` (e.g. with `BM25Retriever` and `Sparse BM25 keyword retriever over all chunks in the store.  Builds an in-memory`) actually correct?**
  _`Chunk` has 37 INFERRED edges - model-reasoned connections that need verification._
- **Are the 33 inferred relationships involving `get()` (e.g. with `test_unknown_component_raises_with_options()` and `query()`) actually correct?**
  _`get()` has 33 INFERRED edges - model-reasoned connections that need verification._