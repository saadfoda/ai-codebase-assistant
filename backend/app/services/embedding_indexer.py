from sqlalchemy.orm import Session

from app.models.code_chunk import CodeChunk
from app.services.embedding_service import embed_code


def embed_pending_chunks(db: Session, repository_id: int) -> int:
    """
    Generate and store embeddings for all code chunks
    belonging to a repository that do not have an embedding yet.
    """

    chunks = (
        db.query(CodeChunk)
        .filter(
            CodeChunk.repository_id == repository_id,
            CodeChunk.embedding.is_(None),
        )
        .all()
    )

    print(f"Found {len(chunks)} chunks without embeddings.")

    embedded_count = 0

    for chunk in chunks:
        print(
            f"Embedding {embedded_count + 1}/{len(chunks)}: "
            f"{chunk.file_path} "
            f"(lines {chunk.start_line}-{chunk.end_line})"
        )

        embedding = embed_code(
            code=chunk.content,
            file_path=chunk.file_path,
        )

        chunk.embedding = embedding

        db.commit()
        embedded_count += 1

    return embedded_count