
import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter

from sqlalchemy.orm import Session

from app.models.code_chunk import CodeChunk
from app.services.repository_service import clone_repository
from app.services.code_parser import read_repository_files
from app.services.code_chunker import chunk_code
from app.services.chunk_service import save_chunks
from app.services.embedding_indexer import generate_chunk_embeddings


logger = logging.getLogger(__name__)


def ingest_repository(
    db: Session,
    repository_id: int,
    repository_url: str,
) -> dict:
    """
    Clone, parse, chunk, and index a GitHub repository.

    Generate all embeddings before replacing the existing
    index in a single database transaction.
    """

    start_time = perf_counter()

    logger.info(
        "Starting ingestion repository_id=%s",
        repository_id,
    )

    try:
        with TemporaryDirectory(
            prefix=f"repository_{repository_id}_"
        ) as temp_dir:

            repository_path = Path(temp_dir) / "source"

            clone_repository(
                repository_url=repository_url,
                destination=str(repository_path),
            )

            files = read_repository_files(
                str(repository_path)
            )

            if not files:
                raise ValueError(
                    "No supported source files were found "
                    "in the repository."
                )

            logger.info(
                "Parsed %s source files repository_id=%s",
                len(files),
                repository_id,
            )

            all_chunks = []

            for file in files:
                file_chunks = chunk_code(
                    content=file["content"],
                    file_path=file["path"],
                )

                all_chunks.extend(file_chunks)

            if not all_chunks:
                raise ValueError(
                    "No code chunks were created "
                    "from the repository."
                )

            logger.info(
                "Created %s chunks repository_id=%s",
                len(all_chunks),
                repository_id,
            )

        logger.info(
            "Temporary repository cleaned up repository_id=%s",
            repository_id,
        )

        # Generate embeddings before modifying existing records.
        embedded_chunks = generate_chunk_embeddings(
            all_chunks
        )

        if len(embedded_chunks) != len(all_chunks):
            raise RuntimeError(
                "Embedding generation returned an "
                "unexpected number of chunks."
            )

        logger.info(
            "Generated %s embeddings repository_id=%s",
            len(embedded_chunks),
            repository_id,
        )

        # Replace the existing index in one transaction.
        db.query(CodeChunk).filter(
            CodeChunk.repository_id == repository_id
        ).delete(synchronize_session=False)

        saved_chunks = save_chunks(
            db=db,
            repository_id=repository_id,
            chunks=embedded_chunks,
        )

        chunks_created = len(saved_chunks)
        embedded_count = len(embedded_chunks)

        # Commit only after all database operations succeed.
        db.commit()

        duration = round(perf_counter() - start_time, 2)

        logger.info(
            "Ingestion completed repository_id=%s "
            "chunks=%s embeddings=%s duration=%.2fs",
            repository_id,
            chunks_created,
            embedded_count,
            duration,
        )

        return {
            "repository_id": repository_id,
            "files_processed": len(files),
            "chunks_created": chunks_created,
            "chunks_embedded": embedded_count,
            "duration_seconds": duration,
        }

    except Exception:
        db.rollback()

        logger.exception(
            "Ingestion failed repository_id=%s",
            repository_id,
        )

        raise
