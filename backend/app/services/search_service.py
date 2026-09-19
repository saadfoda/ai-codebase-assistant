import re

from sqlalchemy.orm import Session

from app.models.code_chunk import CodeChunk
from app.services.embedding_service import embed_query


def search_code(
    db: Session,
    query: str,
    repository_id: int,
    limit: int = 5,
):
    """
    Hybrid code search:
    1. Semantic similarity using pgvector.
    2. Lightweight keyword matching against file paths and code.
    """

    query_embedding = embed_query(query)

    distance = CodeChunk.embedding.cosine_distance(query_embedding)

    # Retrieve more candidates than we ultimately return.
    candidates = (
        db.query(CodeChunk, distance.label("distance"))
        .filter(
            CodeChunk.repository_id == repository_id,
            CodeChunk.embedding.is_not(None),
        )
        .order_by(distance)
        .limit(max(limit * 4, 20))
        .all()
    )

    # Extract useful query terms.
    query_terms = {
        term.lower()
        for term in re.findall(r"[a-zA-Z0-9_]+", query)
        if len(term) >= 3
    }

    reranked = []

    for chunk, vector_distance in candidates:
        path_text = chunk.file_path.lower()
        content_text = chunk.content.lower()

        keyword_score = 0.0

        for term in query_terms:
            if term in path_text:
                keyword_score += 0.20

            if term in content_text:
                keyword_score += 0.05

        # Lower is better.
        final_score = float(vector_distance) - keyword_score

        reranked.append(
            (
                chunk,
                float(vector_distance),
                final_score,
            )
        )

    reranked.sort(key=lambda item: item[2])

    return [
        (chunk, distance)
        for chunk, distance, _ in reranked[:limit]
    ]