from sqlalchemy.orm import Session

from app.models.code_chunk import CodeChunk


def save_chunks(
    db: Session,
    repository_id: int,
    chunks: list[dict],
) -> list[CodeChunk]:
    saved_chunks = []

    for chunk in chunks:
        db_chunk = CodeChunk(
            repository_id=repository_id,
            file_path=chunk["file_path"],
            chunk_index=chunk["chunk_index"],
            start_line=chunk["start_line"],
            end_line=chunk["end_line"],
            content=chunk["content"],
        )

        db.add(db_chunk)
        saved_chunks.append(db_chunk)

    db.commit()

    for chunk in saved_chunks:
        db.refresh(chunk)

    return saved_chunks