from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routes.repositories import router as repositories_router


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="AI Codebase Assistant",
    description="AI-powered assistant for understanding and analyzing codebases.",
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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