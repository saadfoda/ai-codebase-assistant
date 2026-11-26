
from sqlalchemy.orm import Session

from app.models.code_chunk import CodeChunk


def save_chunks(
    db: Session,
    repository_id: int,
    chunks: list[dict],
) -> list[CodeChunk]:
    """
    Save fully embedded code chunks.

    Transaction management is handled by the caller.
    """

    saved_chunks = []

    for chunk in chunks:
        db_chunk = CodeChunk(
            repository_id=repository_id,
            file_path=chunk["file_path"],
            chunk_index=chunk["chunk_index"],
            start_line=chunk["start_line"],
            end_line=chunk["end_line"],
            content=chunk["content"],
            embedding=chunk["embedding"],
        )

        db.add(db_chunk)
        saved_chunks.append(db_chunk)

    db.flush()

    return saved_chunks
