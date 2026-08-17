from fastapi import FastAPI

from .database import Base, engine
from .models.models import Repository
from .models.code_chunk import CodeChunk
from .routes.repositories import router as repositories_router


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="AI Codebase Assistant",
    description="AI-powered assistant for understanding and analyzing codebases.",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "project": "AI Codebase Assistant",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "ai-codebase-assistant",
    }


app.include_router(repositories_router)