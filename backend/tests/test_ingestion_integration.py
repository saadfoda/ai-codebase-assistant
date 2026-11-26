
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import Base
from app.models.models import Repository
from app.models.code_chunk import CodeChunk
from app.services.ingestion_service import ingest_repository


MODULE = "app.services.ingestion_service"

TEST_DATABASE_URL = (
    "postgresql+psycopg://testuser:testpassword"
    "@127.0.0.1:5433/codebase_test"
)

REPOSITORY_URL = "https://github.com/user/repository"
VALID_EMBEDDING = [0.1] * 768


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DB_INTEGRATION_TESTS") != "1",
    reason="Local PostgreSQL integration tests are opt-in",
)


@pytest.fixture
def db():
    engine = create_engine(TEST_DATABASE_URL)

    try:
        Base.metadata.create_all(engine)

        with Session(engine) as session:
            yield session

    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def repository_id(db):
    repository = Repository(
        url=REPOSITORY_URL,
        name="test-repository",
        description="Integration test repository",
    )

    db.add(repository)
    db.commit()
    db.refresh(repository)

    return repository.id


def fake_clone(repository_url, destination):
    path = Path(destination)
    path.mkdir()

    (path / "main.py").write_text(
        "print('new code')",
        encoding="utf-8",
    )

    return str(path)


def fake_embeddings(chunks):
    return [
        {
            **chunk,
            "embedding": VALID_EMBEDDING,
        }
        for chunk in chunks
    ]


def seed_existing_chunk(db, repository_id):
    chunk = CodeChunk(
        repository_id=repository_id,
        file_path="old.py",
        chunk_index=0,
        start_line=1,
        end_line=1,
        content="print('old code')",
        embedding=VALID_EMBEDDING,
    )

    db.add(chunk)
    db.commit()


def get_chunks(db, repository_id):
    return (
        db.query(CodeChunk)
        .filter(CodeChunk.repository_id == repository_id)
        .all()
    )


def test_initial_indexing(db, repository_id):
    with (
        patch(
            f"{MODULE}.clone_repository",
            side_effect=fake_clone,
        ),
        patch(
            f"{MODULE}.generate_chunk_embeddings",
            side_effect=fake_embeddings,
        ),
    ):
        result = ingest_repository(
            db=db,
            repository_id=repository_id,
            repository_url=REPOSITORY_URL,
        )

    chunks = get_chunks(db, repository_id)

    assert result["chunks_created"] == 1
    assert result["chunks_embedded"] == 1
    assert len(chunks) == 1
    assert chunks[0].file_path == "main.py"
    assert len(chunks[0].embedding) == 768


def test_successful_reindex_replaces_old_chunks(
    db, repository_id
):
    seed_existing_chunk(db, repository_id)

    with (
        patch(
            f"{MODULE}.clone_repository",
            side_effect=fake_clone,
        ),
        patch(
            f"{MODULE}.generate_chunk_embeddings",
            side_effect=fake_embeddings,
        ),
    ):
        ingest_repository(
            db=db,
            repository_id=repository_id,
            repository_url=REPOSITORY_URL,
        )

    chunks = get_chunks(db, repository_id)

    assert len(chunks) == 1
    assert chunks[0].file_path == "main.py"
    assert chunks[0].content == "print('new code')"


def test_embedding_failure_preserves_existing_index(
    db, repository_id
):
    seed_existing_chunk(db, repository_id)

    with (
        patch(
            f"{MODULE}.clone_repository",
            side_effect=fake_clone,
        ),
        patch(
            f"{MODULE}.generate_chunk_embeddings",
            side_effect=RuntimeError("Embedding failed"),
        ),
    ):
        with pytest.raises(
            RuntimeError,
            match="Embedding failed",
        ):
            ingest_repository(
                db=db,
                repository_id=repository_id,
                repository_url=REPOSITORY_URL,
            )

    chunks = get_chunks(db, repository_id)

    assert len(chunks) == 1
    assert chunks[0].file_path == "old.py"
    assert chunks[0].content == "print('old code')"


def test_database_failure_restores_existing_index(
    db, repository_id
):
    seed_existing_chunk(db, repository_id)

    def invalid_embeddings(chunks):
        return [
            {
                **chunk,
                "file_path": None,
                "embedding": VALID_EMBEDDING,
            }
            for chunk in chunks
        ]

    with (
        patch(
            f"{MODULE}.clone_repository",
            side_effect=fake_clone,
        ),
        patch(
            f"{MODULE}.generate_chunk_embeddings",
            side_effect=invalid_embeddings,
        ),
    ):
        with pytest.raises(IntegrityError):
            ingest_repository(
                db=db,
                repository_id=repository_id,
                repository_url=REPOSITORY_URL,
            )

    chunks = get_chunks(db, repository_id)

    assert len(chunks) == 1
    assert chunks[0].file_path == "old.py"
    assert chunks[0].content == "print('old code')"
    assert len(chunks[0].embedding) == 768
