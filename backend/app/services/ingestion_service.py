from pathlib import Path
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.code_chunk import CodeChunk
from app.services.repository_service import clone_repository
from app.services.code_parser import read_repository_files
from app.services.code_chunker import chunk_code
from app.services.chunk_service import save_chunks
from app.services.embedding_indexer import embed_pending_chunks


def ingest_repository(
    db: Session,
    repository_id: int,
    repository_url: str,
) -> dict:
    """
    Clone a GitHub repository, parse its source files, chunk the code,
    save the chunks, and generate embeddings.

    Each ingestion uses a unique local clone directory so that
    Windows file locks on previous Git clones do not prevent re-indexing.
    """

    project_root = Path(__file__).resolve().parents[3]

    cloned_repositories_dir = project_root / "cloned_repositories"
    cloned_repositories_dir.mkdir(parents=True, exist_ok=True)

    repository_path = (
        cloned_repositories_dir
        / f"repository_{repository_id}_{uuid4().hex[:8]}"
    )

    # Clone repository
    clone_repository(
        repository_url=repository_url,
        destination=str(repository_path),
    )

    # Read supported source files
    files = read_repository_files(str(repository_path))

    if not files:
        raise ValueError(
            "No supported source files were found in the repository."
        )

    # Chunk all source files
    all_chunks = []

    for file in files:
        file_chunks = chunk_code(
            content=file["content"],
            file_path=file["path"],
        )

        all_chunks.extend(file_chunks)

    if not all_chunks:
        raise ValueError(
            "No code chunks were created from the repository."
        )

    # Remove old indexed chunks only after the new repository
    # has been successfully cloned and processed.
    db.query(CodeChunk).filter(
        CodeChunk.repository_id == repository_id
    ).delete(synchronize_session=False)

    db.commit()

    # Save new chunks
    saved_chunks = save_chunks(
        db=db,
        repository_id=repository_id,
        chunks=all_chunks,
    )

    # Generate and store embeddings
    embedded_count = embed_pending_chunks(
        db=db,
        repository_id=repository_id,
    )

    return {
        "repository_id": repository_id,
        "repository_path": str(repository_path),
        "files_processed": len(files),
        "chunks_created": len(saved_chunks),
        "chunks_embedded": embedded_count,
    }