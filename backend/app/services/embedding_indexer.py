
import logging

from app.services.embedding_service import embed_code


logger = logging.getLogger(__name__)


def generate_chunk_embeddings(
    chunks: list[dict],
) -> list[dict]:
    """
    Generate embeddings for all code chunks before
    modifying the database.
    """

    embedded_chunks = []
    total_chunks = len(chunks)

    logger.info(
        "Generating embeddings for %s chunks",
        total_chunks,
    )

    for index, chunk in enumerate(chunks, start=1):
        logger.info(
            "Embedding %s/%s: %s (lines %s-%s)",
            index,
            total_chunks,
            chunk["file_path"],
            chunk["start_line"],
            chunk["end_line"],
        )

        embedding = embed_code(
            code=chunk["content"],
            file_path=chunk["file_path"],
        )

        embedded_chunks.append({
            **chunk,
            "embedding": embedding,
        })

    logger.info(
        "Successfully generated %s embeddings",
        len(embedded_chunks),
    )

    return embedded_chunks
