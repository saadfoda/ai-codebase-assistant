
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.services.ingestion_service import ingest_repository


MODULE = "app.services.ingestion_service"
REPOSITORY_URL = "https://github.com/user/repository"


def test_ingestion_cleans_up_after_success():
    db = MagicMock()
    paths = []

    def fake_clone(repository_url, destination):
        path = Path(destination)
        path.mkdir()
        (path / "main.py").write_text(
            "print('hello')", encoding="utf-8"
        )
        paths.append(path)
        return str(path)

    with (
        patch(
            f"{MODULE}.clone_repository",
            side_effect=fake_clone,
        ),
        patch(
            f"{MODULE}.save_chunks",
            return_value=[MagicMock()],
        ),
        patch(
            f"{MODULE}.embed_pending_chunks",
            return_value=1,
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
        with pytest.raises(RuntimeError, match="Clone failed"):
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

    def fake_clone(repository_url, destination):
        path = Path(destination)
        path.mkdir()
        paths.append(path)
        return str(path)

    with patch(
        f"{MODULE}.clone_repository",
        side_effect=fake_clone,
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
