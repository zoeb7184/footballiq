"""RAG analyst pipeline (Module 7). Pure application logic over ports.

Core rule (rag-design): numbers never come from embeddings. Semantic retrieval
finds definitions and routes; every numeric fact comes from executed SQL. This
package holds the chunking, indexing orchestration, and ports; adapters
(embeddings, vector store) live in infrastructure.ai.
"""
