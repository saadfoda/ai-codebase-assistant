import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types


# Find backend/.env regardless of where the application is started from.
BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY is not set in backend/.env")

client = genai.Client(api_key=api_key)

MODEL = "gemini-embedding-2"
EMBEDDING_DIMENSIONS = 768


def embed_code(code: str, file_path: str) -> list[float]:
    """
    Generate a semantic embedding for a source-code chunk.
    """

    text = (
        "Represent this source code for semantic code search.\n"
        f"File: {file_path}\n\n"
        f"{code}"
    )

    response = client.models.embed_content(
        model=MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            output_dimensionality=EMBEDDING_DIMENSIONS
        ),
    )

    if not response.embeddings:
        raise RuntimeError("Gemini returned no embedding")

    values = response.embeddings[0].values

    if values is None:
        raise RuntimeError("Gemini returned an embedding with no values")

    if len(values) != EMBEDDING_DIMENSIONS:
        raise RuntimeError(
            f"Expected {EMBEDDING_DIMENSIONS} dimensions, "
            f"but received {len(values)}"
        )

    return values

def embed_query(query: str) -> list[float]:
    """
    Generate an embedding for a natural-language code search query.
    """

    text = (
        "Represent this natural-language query for semantic code search.\n\n"
        f"{query}"
    )

    response = client.models.embed_content(
        model=MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            output_dimensionality=EMBEDDING_DIMENSIONS
        ),
    )

    if not response.embeddings:
        raise RuntimeError("Gemini returned no embedding")

    values = response.embeddings[0].values

    if values is None:
        raise RuntimeError("Gemini returned an embedding with no values")

    if len(values) != EMBEDDING_DIMENSIONS:
        raise RuntimeError(
            f"Expected {EMBEDDING_DIMENSIONS} dimensions, "
            f"but received {len(values)}"
        )

    return values