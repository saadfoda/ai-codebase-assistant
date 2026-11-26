
from unittest.mock import MagicMock, patch

import pytest

from app.services.chunk_service import save_chunks
from app.services.embedding_indexer import generate_chunk_embeddings


VALID_EMBEDDING = [0.1] * 768

SAMPLE_CHUNK = {
    "file_path": "main.py",
    "chunk_index": 0,
    "start_line": 1,
    "end_line": 1,
    "content": "print('hello')",
}


def test_generate_chunk_embeddings_success():
    chunks = [SAMPLE_CHUNK.copy()]

    with patch(
        "app.services.embedding_indexer.embed_code",
        return_value=VALID_EMBEDDING,
    ) as mock_embed:
        result = generate_chunk_embeddings(chunks)

    assert len(result) == 1
    assert result[0]["embedding"] == VALID_EMBEDDING
    assert result[0]["file_path"] == "main.py"
    assert "embedding" not in chunks[0]

    mock_embed.assert_called_once_with(
        code="print('hello')",
        file_path="main.py",
    )


def test_generate_chunk_embeddings_failure():
    chunks = [
        SAMPLE_CHUNK.copy(),
        SAMPLE_CHUNK.copy(),
    ]

    with patch(
        "app.services.embedding_indexer.embed_code",
        side_effect=[
            VALID_EMBEDDING,
            RuntimeError("Embedding failed"),
        ],
    ) as mock_embed:
        with pytest.raises(
            RuntimeError,
            match="Embedding failed",
        ):
            generate_chunk_embeddings(chunks)

    assert mock_embed.call_count == 2
    assert all(
        "embedding" not in chunk
        for chunk in chunks
    )


def test_save_chunks_stores_embeddings_without_commit():
    db = MagicMock()

    chunks = [
        {
            **SAMPLE_CHUNK,
            "embedding": VALID_EMBEDDING,
        }
    ]

    result = save_chunks(
        db=db,
        repository_id=1,
        chunks=chunks,
    )

    assert len(result) == 1
    assert result[0].repository_id == 1
    assert result[0].file_path == "main.py"
    assert result[0].embedding == VALID_EMBEDDING

    db.add.assert_called_once_with(result[0])
    db.flush.assert_called_once()
    db.commit.assert_not_called()


def test_save_chunks_propagates_database_failure():
    db = MagicMock()

    db.flush.side_effect = RuntimeError(
        "Database flush failed"
    )

    chunks = [
        {
            **SAMPLE_CHUNK,
            "embedding": VALID_EMBEDDING,
        }
    ]

    with pytest.raises(
        RuntimeError,
        match="Database flush failed",
    ):
        save_chunks(
            db=db,
            repository_id=1,
            chunks=chunks,
        )

    db.commit.assert_not_called()
    db.rollback.assert_not_called()
