---
type: community
members: 75
---

# Core Interfaces & Types

**Members:** 75 nodes

## Members
- [[.__init__()_1]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/retrievers/dense.py
- [[.__init__()_7]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/ingestion/chunkers/recursive.py
- [[.all_chunks()]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/interfaces.py
- [[.chunk()_3]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/interfaces.py
- [[.ensure_collection()]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/interfaces.py
- [[.evaluate()]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/interfaces.py
- [[.generate()]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/interfaces.py
- [[.model_post_init()]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/config.py
- [[.rerank()]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/interfaces.py
- [[.run()]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/interfaces.py
- [[.search()]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/interfaces.py
- [[.upsert()]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/interfaces.py
- [[A chunk paired with a retrievalrerank score.]] - rationale - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/types.py
- [[A complete RAG architecture. Every architecture conforms to this.]] - rationale - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/interfaces.py
- [[A knowledge graph built from documents (entities + relationships).]] - rationale - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/graph/__init__.py
- [[A parsed source document, before chunking.]] - rationale - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/types.py
- [[A retrievable unit of text with provenance metadata.      Metadata conventionall]] - rationale - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/types.py
- [[An LLM generation result that carries usage so cost can be computed.]] - rationale - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/types.py
- [[Build the architecture pipeline around an already-resolved component set.      L]] - rationale - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/config.py
- [[Chatcompletion model that reports token usage and cost.]] - rationale - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/interfaces.py
- [[Chunk]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/types.py
- [[Chunker]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/interfaces.py
- [[Component contracts.  Every swappable part of RAGLab is defined here as a ``Prot]] - rationale - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/interfaces.py
- [[Components]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/config.py
- [[Dense vector retriever — embeds the query and searches the vector store.]] - rationale - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/retrievers/dense.py
- [[DenseRetriever]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/retrievers/dense.py
- [[Document]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/types.py
- [[Embedder]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/interfaces.py
- [[Evaluator]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/interfaces.py
- [[ExperimentConfig]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/config.py
- [[IngestResult]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/ingestion/pipeline.py
- [[Ingestion flow Documents - Parser - Cleaner - Chunker - Enrich - Embed -]] - rationale - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/ingestion/pipeline.py
- [[LLM]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/interfaces.py
- [[LLMResponse]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/types.py
- [[Large parent chunks split into smaller child chunks; children carry a     ``pare]] - rationale - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/ingestion/chunkers/recursive.py
- [[Maps text to dense vectors.]] - rationale - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/interfaces.py
- [[ParentChildChunker]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/ingestion/chunkers/recursive.py
- [[Parser]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/interfaces.py
- [[Pipeline]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/interfaces.py
- [[Protocol]] - code
- [[RAGResult]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/types.py
- [[Reorders candidate chunks for a query.]] - rationale - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/interfaces.py
- [[Reranker]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/interfaces.py
- [[Resolve the full architecture pipeline from config.]] - rationale - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/config.py
- [[Resolved, wired components ready to hand to a pipeline.]] - rationale - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/config.py
- [[Retriever]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/interfaces.py
- [[Return the first registered parser that supports ``path``.]] - rationale - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/ingestion/parsers/__init__.py
- [[Returns scored chunks relevant to a query.]] - rationale - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/interfaces.py
- [[ScoredChunk]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/types.py
- [[Scores a batch of (question, answer, contexts, ground_truth) records.]] - rationale - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/interfaces.py
- [[Shared data structures that flow between every RAGLab component.  These are deli]] - rationale - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/types.py
- [[Splits documents into retrievable chunks.]] - rationale - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/interfaces.py
- [[Stores chunk vectors and answers nearest-neighbour queries.]] - rationale - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/interfaces.py
- [[The uniform output of every architecture's ``Pipeline.run``.]] - rationale - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/types.py
- [[Turns a file on disk into one or more class`Document` objects.]] - rationale - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/interfaces.py
- [[Typed configuration + the composition root.  A YAML experiment file is parsed in]] - rationale - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/config.py
- [[VectorStore]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/interfaces.py
- [[context_texts()]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/types.py
- [[dense.py]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/retrievers/dense.py
- [[dense.py_1]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/retrievers/dense.py
- [[dim()_4]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/interfaces.py
- [[interfaces.py]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/interfaces.py
- [[interfaces.py_1]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/interfaces.py
- [[model()]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/interfaces.py
- [[pipeline.py]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/ingestion/pipeline.py
- [[pipeline.py_1]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/ingestion/pipeline.py
- [[source()]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/types.py
- [[test_chunkers.py]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/tests/unit/test_chunkers.py
- [[test_chunkers.py_1]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/tests/unit/test_chunkers.py
- [[test_parent_child_carries_parent_text()]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/tests/unit/test_chunkers.py
- [[test_recursive_chunker_respects_size()]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/tests/unit/test_chunkers.py
- [[text()]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/types.py
- [[total_tokens()]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/types.py
- [[types.py]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/types.py
- [[types.py_1]] - code - /Users/saniyasultanatuba/Downloads/05_Project_Files/dev/agentic-rag-evaluations/raglab/src/raglab/core/types.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Core_Interfaces_&_Types
SORT file.name ASC
```

## Connections to other communities
- 54 edges to [[_COMMUNITY_Configuration & CLI]]
- 35 edges to [[_COMMUNITY_RAG Pipelines]]
- 15 edges to [[_COMMUNITY_Retrieval & Vector Store]]
- 14 edges to [[_COMMUNITY_API Service & Observability]]
- 11 edges to [[_COMMUNITY_Fusion & Multi-Query]]
- 11 edges to [[_COMMUNITY_CLI & Ingestion]]
- 10 edges to [[_COMMUNITY_Package Initializers]]
- 9 edges to [[_COMMUNITY_Recursive Chunkers]]
- 7 edges to [[_COMMUNITY_Text Parsers]]
- 5 edges to [[_COMMUNITY_PDF & DOCX Parsers]]
- 5 edges to [[_COMMUNITY_LLM & Evaluation Judges]]
- 5 edges to [[_COMMUNITY_Agent Critic & Grading]]
- 5 edges to [[_COMMUNITY_OpenAI-Compatible LLMs & Costs]]
- 3 edges to [[_COMMUNITY_Cohere Reranker]]
- 3 edges to [[_COMMUNITY_Cross-Encoder Reranker]]
- 2 edges to [[_COMMUNITY_Timer Utility]]
- 1 edge to [[_COMMUNITY_Benchmarking & Evaluation]]
- 1 edge to [[_COMMUNITY_Pipeline Stubs]]

## Top bridge nodes
- [[ScoredChunk]] - degree 62, connects to 7 communities
- [[Embedder]] - degree 33, connects to 5 communities
- [[Document]] - degree 45, connects to 4 communities
- [[Chunk]] - degree 40, connects to 4 communities
- [[VectorStore]] - degree 35, connects to 4 communities