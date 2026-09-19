from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Repository
from app.schemas.repository import RepositoryCreate, RepositoryResponse
from app.services.search_service import search_code
from app.services.answer_service import generate_answer


router = APIRouter(
    prefix="/repositories",
    tags=["Repositories"],
)


@router.post("/", response_model=RepositoryResponse)
def create_repository(
    repository: RepositoryCreate,
    db: Session = Depends(get_db),
):
    existing_repository = (
        db.query(Repository)
        .filter(Repository.url == str(repository.url))
        .first()
    )

    if existing_repository:
        return existing_repository

    db_repository = Repository(
        url=str(repository.url),
        name=repository.name,
        description=repository.description,
    )

    db.add(db_repository)
    db.commit()
    db.refresh(db_repository)

    return db_repository


@router.get("/{repository_id}/search")
def search_repository(
    repository_id: int,
    q: str = Query(..., min_length=1),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    repository = (
        db.query(Repository)
        .filter(Repository.id == repository_id)
        .first()
    )

    if not repository:
        raise HTTPException(
            status_code=404,
            detail="Repository not found",
        )

    results = search_code(
        db=db,
        query=q,
        repository_id=repository_id,
        limit=limit,
    )

    return {
        "repository_id": repository_id,
        "query": q,
        "results": [
            {
                "file_path": chunk.file_path,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "content": chunk.content,
                "distance": float(distance),
            }
            for chunk, distance in results
        ],
    }

@router.get("/{repository_id}/ask")
def ask_repository(
    repository_id: int,
    q: str = Query(..., min_length=1),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    repository = (
        db.query(Repository)
        .filter(Repository.id == repository_id)
        .first()
    )

    if not repository:
        raise HTTPException(
            status_code=404,
            detail="Repository not found",
        )

    results = search_code(
        db=db,
        query=q,
        repository_id=repository_id,
        limit=limit,
    )

    answer = generate_answer(q, results)

    return {
        "repository_id": repository_id,
        "query": q,
        "answer": answer,
        "sources": [
            {
                "file_path": chunk.file_path,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "distance": float(distance),
            }
            for chunk, distance in results
        ],
    }