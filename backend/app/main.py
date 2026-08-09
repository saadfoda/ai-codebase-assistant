from fastapi import FastAPI

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