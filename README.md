# AI Codebase Assistant

[![Backend CI](https://github.com/saadfoda/ai-codebase-assistant/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/saadfoda/ai-codebase-assistant/actions/workflows/backend-ci.yml)

A full-stack, retrieval-augmented generation (RAG) application that helps developers understand unfamiliar GitHub codebases through natural-language questions and source-grounded answers.

**[Live demo](https://ai-codebase-assistant-nu.vercel.app/)** | **[Backend API documentation](https://ai-codebase-assistant-5mf0.onrender.com/docs)**

## Features

- Ingest GitHub repositories and parse supported source-code files.
- Split source code into chunks and generate semantic embeddings with Gemini.
- Retrieve relevant code using hybrid semantic and keyword search with PostgreSQL and pgvector.
- Generate answers using retrieved code context, with source file paths and line-range citations.
- Interact with repositories through a Next.js frontend and FastAPI REST API.
- Run automated backend tests and Docker build verification through GitHub Actions.

## Technology stack

| Layer | Technologies |
| --- | --- |
| Frontend | Next.js, React, TypeScript, Tailwind CSS |
| Backend | Python, FastAPI, SQLAlchemy |
| Database | PostgreSQL, pgvector |
| AI | Google Gemini API, embeddings, RAG |
| Testing | pytest, FastAPI TestClient, mocked dependencies |
| DevOps | Docker, GitHub Actions |
| Hosting | Vercel, Render |

## Architecture

```mermaid
flowchart TD
    A[GitHub repository] --> B[Git clone]
    B --> C[Source-code parsing]
    C --> D[Code chunking]
    D --> E[Gemini embeddings]
    E --> F[(PostgreSQL + pgvector)]
    G[Next.js frontend] --> H[FastAPI]
    H --> I[Hybrid retrieval]
    F --> I
    I --> J[Relevant code context]
    J --> K[Gemini answer generation]
    K --> H
    H --> L[Answer and source citations]
```

The ingestion pipeline indexes repository content. At query time, the backend retrieves relevant chunks and supplies them to Gemini as context, rather than sending the entire repository with every question.

## Getting started

### Prerequisites

- Docker Desktop (or Python 3.12 and Git for a native backend setup)
- Node.js 20.9+ and npm
- PostgreSQL database with the pgvector extension enabled
- Gemini API key

### 1. Clone the repository

```bash
git clone https://github.com/saadfoda/ai-codebase-assistant.git
cd ai-codebase-assistant
cp backend/.env.example backend/.env
```

Configure `backend/.env` with your own database connection and Gemini API key. Keep this file private. When using Docker, ensure the database is reachable from inside the container; a database running on the host may require `host.docker.internal` on Docker Desktop.

### 2. Start the backend with Docker

```bash
docker build -t ai-codebase-backend ./backend
docker run --rm --name ai-codebase-container --env-file backend/.env -p 8000:8000 ai-codebase-backend
```

- Health check: http://localhost:8000/health
- Swagger API documentation: http://localhost:8000/docs

### 3. Start the frontend

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000. The frontend defaults to the local backend at `http://127.0.0.1:8000`. Set `NEXT_PUBLIC_API_BASE_URL` in `frontend/.env.local` if you need a different backend URL.

### 4. Try the application

Add a small public GitHub repository, ingest it, and ask a question such as:

> Where is the main application logic implemented?

Inspect the returned answer and source citations to locate the relevant implementation.

## API endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/health` | Service health check |
| GET | `/repositories/` | List repositories |
| POST | `/repositories/` | Register a repository |
| POST | `/repositories/{repository_id}/ingest` | Index repository content |
| GET | `/repositories/{repository_id}/search` | Retrieve relevant code |
| GET | `/repositories/{repository_id}/ask` | Generate an answer with sources |

## Testing and continuous integration

The [Backend CI workflow](https://github.com/saadfoda/ai-codebase-assistant/actions/workflows/backend-ci.yml) runs on pushes and pull requests targeting `main`. It installs Python dependencies, executes pytest, and builds the Docker image.

To run the existing tests locally from the repository root using Git Bash:

```bash
cd backend
python -m pip install -r requirements.txt
DATABASE_URL=postgresql://test:test@localhost:5432/test_db GEMINI_API_KEY=dummy-test-key python -m pytest tests/ -v
```

API tests use fake database dependencies and mocked AI and ingestion functions. These tests validate API behavior without requiring production credentials; they do not replace live integration tests.

## Project structure

```text
ai-codebase-assistant/
├── .github/workflows/backend-ci.yml
├── backend/
│   ├── app/
│   │   ├── models/
│   │   ├── routes/
│   │   ├── schemas/
│   │   └── services/
│   ├── tests/
│   ├── Dockerfile
│   ├── .dockerignore
│   └── requirements.txt
└── frontend/
```

## Future improvements

- End-to-end integration tests using an isolated test database.
- Improved ingestion reliability, error handling, and temporary-file cleanup.
- CI-gated continuous deployment.
