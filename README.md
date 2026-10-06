AI Codebase Assistant

A RAG-powered application for asking natural-language questions
about GitHub codebases.

Features
- GitHub repository ingestion
- Source-code parsing and chunking
- Gemini embeddings
- PostgreSQL + pgvector semantic search
- Hybrid semantic/keyword retrieval
- Gemini-powered RAG answers
- Source file + line-range citations
- Next.js frontend
- FastAPI backend
- Automated tests

Architecture
GitHub Repository
       ↓
Clone
       ↓
Parse Source Files
       ↓
Chunk Code
       ↓
Gemini Embeddings
       ↓
PostgreSQL + pgvector
       ↓
Hybrid Search
       ↓
Relevant Code Context
       ↓
Gemini
       ↓
Answer + Sources