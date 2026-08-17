from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Repository
from app.schemas.repository import RepositoryCreate, RepositoryResponse


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