
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.services.ingestion_service import ingest_repository


MODULE = "app.services.ingestion_service"
REPOSITORY_URL = "https://github.com/user/repository"
VALID_EMBEDDING = [0.1] * 768


def fake_clone(repository_url, destination):
    path = Path(destination)
    path.mkdir()

    (path / "main.py").write_text(
        "print('hello')",
        encoding="utf-8",
    )

    return str(path)


def fake_generate_embeddings(chunks):
    return [
        {
            **chunk,
            "embedding": VALID_EMBEDDING,
        }
        for chunk in chunks
    ]


def test_ingestion_cleans_up_after_success():
    db = MagicMock()
    paths = []

    def tracked_clone(repository_url, destination):
        paths.append(Path(destination))
        return fake_clone(repository_url, destination)

    def tracked_embeddings(chunks):
        # No database modifications before embeddings.
        db.query.assert_not_called()
        db.commit.assert_not_called()

        return fake_generate_embeddings(chunks)

    with (
        patch(
            f"{MODULE}.clone_repository",
            side_effect=tracked_clone,
        ),
        patch(
            f"{MODULE}.save_chunks",
            return_value=[MagicMock()],
        ) as mock_save,
        patch(
            f"{MODULE}.generate_chunk_embeddings",
            side_effect=tracked_embeddings,
        ),
    ):
        result = ingest_repository(
            db=db,
            repository_id=1,
            repository_url=REPOSITORY_URL,
        )

    assert len(paths) == 1
    assert not paths[0].exists()
    assert not paths[0].parent.exists()

    assert result["files_processed"] == 1
    assert result["chunks_created"] == 1
    assert result["chunks_embedded"] == 1
    assert result["duration_seconds"] >= 0
    assert "repository_path" not in result

    saved_chunks = mock_save.call_args.kwargs["chunks"]

    assert len(saved_chunks) == 1
    assert saved_chunks[0]["embedding"] == VALID_EMBEDDING

    db.query.return_value.filter.return_value.delete.assert_called_once_with(
        synchronize_session=False
    )

    db.commit.assert_called_once()
    db.rollback.assert_not_called()


def test_ingestion_cleans_up_after_clone_failure():
    db = MagicMock()
    paths = []

    def failing_clone(repository_url, destination):
        path = Path(destination)
        path.mkdir()
        paths.append(path)

        raise RuntimeError("Clone failed")

    with patch(
        f"{MODULE}.clone_repository",
        side_effect=failing_clone,
    ):
        with pytest.raises(
            RuntimeError,
            match="Clone failed",
        ):
            ingest_repository(
                db=db,
                repository_id=1,
                repository_url=REPOSITORY_URL,
            )

    assert len(paths) == 1
    assert not paths[0].exists()
    assert not paths[0].parent.exists()

    db.rollback.assert_called_once()
    db.query.assert_not_called()
    db.commit.assert_not_called()


def test_ingestion_cleans_up_empty_repository():
    db = MagicMock()
    paths = []

    def empty_clone(repository_url, destination):
        path = Path(destination)
        path.mkdir()
        paths.append(path)

        return str(path)

    with patch(
        f"{MODULE}.clone_repository",
        side_effect=empty_clone,
    ):
        with pytest.raises(
            ValueError,
            match="No supported source files",
        ):
            ingest_repository(
                db=db,
                repository_id=1,
                repository_url=REPOSITORY_URL,
            )

    assert len(paths) == 1
    assert not paths[0].exists()
    assert not paths[0].parent.exists()

    db.rollback.assert_called_once()
    db.query.assert_not_called()
    db.commit.assert_not_called()


def test_ingestion_preserves_index_on_embedding_failure():
    db = MagicMock()

    with (
        patch(
            f"{MODULE}.clone_repository",
            side_effect=fake_clone,
        ),
        patch(
            f"{MODULE}.generate_chunk_embeddings",
            side_effect=RuntimeError("Embedding failed"),
        ),
        patch(
            f"{MODULE}.save_chunks",
        ) as mock_save,
    ):
        with pytest.raises(
            RuntimeError,
            match="Embedding failed",
        ):
            ingest_repository(
                db=db,
                repository_id=1,
                repository_url=REPOSITORY_URL,
            )

    db.query.assert_not_called()
    mock_save.assert_not_called()
    db.commit.assert_not_called()
    db.rollback.assert_called_once()


def test_ingestion_rolls_back_on_database_failure():
    db = MagicMock()

    with (
        patch(
            f"{MODULE}.clone_repository",
            side_effect=fake_clone,
        ),
        patch(
            f"{MODULE}.generate_chunk_embeddings",
            side_effect=fake_generate_embeddings,
        ),
        patch(
            f"{MODULE}.save_chunks",
            side_effect=RuntimeError("Database write failed"),
        ),
    ):
        with pytest.raises(
            RuntimeError,
            match="Database write failed",
        ):
            ingest_repository(
                db=db,
                repository_id=1,
                repository_url=REPOSITORY_URL,
            )

    db.query.return_value.filter.return_value.delete.assert_called_once()

    db.commit.assert_not_called()
    db.rollback.assert_called_once()


def test_ingestion_rolls_back_on_commit_failure():
    db = MagicMock()

    db.commit.side_effect = RuntimeError("Commit failed")

    with (
        patch(
            f"{MODULE}.clone_repository",
            side_effect=fake_clone,
        ),
        patch(
            f"{MODULE}.generate_chunk_embeddings",
            side_effect=fake_generate_embeddings,
        ),
        patch(
            f"{MODULE}.save_chunks",
            return_value=[MagicMock()],
        ),
    ):
        with pytest.raises(
            RuntimeError,
            match="Commit failed",
        ):
            ingest_repository(
                db=db,
                repository_id=1,
                repository_url=REPOSITORY_URL,
            )

    db.commit.assert_called_once()
    db.rollback.assert_called_once()
