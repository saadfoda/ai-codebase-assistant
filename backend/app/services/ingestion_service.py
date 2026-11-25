
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
from app.services.embedding_indexer import embed_pending_chunks

logger = logging.getLogger(__name__)


def ingest_repository(
    db: Session,
    repository_id: int,
    repository_url: str,
) -> dict:
    """
    Clone, parse, chunk, and index a GitHub repository.
    Temporary repository files are automatically cleaned up.
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

        db.query(CodeChunk).filter(
            CodeChunk.repository_id == repository_id
        ).delete(synchronize_session=False)

        db.commit()

        saved_chunks = save_chunks(
            db=db,
            repository_id=repository_id,
            chunks=all_chunks,
        )

        embedded_count = embed_pending_chunks(
            db=db,
            repository_id=repository_id,
        )

        duration = round(perf_counter() - start_time, 2)

        logger.info(
            "Ingestion completed repository_id=%s "
            "chunks=%s embeddings=%s duration=%.2fs",
            repository_id,
            len(saved_chunks),
            embedded_count,
            duration,
        )

        return {
            "repository_id": repository_id,
            "files_processed": len(files),
            "chunks_created": len(saved_chunks),
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
