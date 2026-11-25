import logging
import os
import random
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types


logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY is not set")

client = genai.Client(api_key=api_key)

MODEL = "gemini-embedding-2"
EMBEDDING_DIMENSIONS = 768

MAX_ATTEMPTS = 4
INITIAL_RETRY_DELAY = 30
MAX_RETRY_DELAY = 120

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def generate_embedding(text: str) -> list[float]:
    """
    Generate an embedding with bounded retries for
    temporary Gemini API failures.
    """

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = client.models.embed_content(
                model=MODEL,
                contents=text,
                config=types.EmbedContentConfig(
                    output_dimensionality=EMBEDDING_DIMENSIONS
                ),
            )

            if not response.embeddings:
                raise RuntimeError(
                    "Gemini returned no embedding"
                )

            values = response.embeddings[0].values

            if values is None:
                raise RuntimeError(
                    "Gemini returned an embedding with no values"
                )

            if len(values) != EMBEDDING_DIMENSIONS:
                raise RuntimeError(
                    f"Expected {EMBEDDING_DIMENSIONS} dimensions, "
                    f"but received {len(values)}"
                )

            return values

        except errors.APIError as exc:
            status_code = exc.code

            if status_code not in RETRYABLE_STATUS_CODES:
                raise

            if attempt == MAX_ATTEMPTS:
                logger.error(
                    "Embedding failed after %s attempts "
                    "status_code=%s",
                    MAX_ATTEMPTS,
                    status_code,
                )
                raise

            delay = min(
                INITIAL_RETRY_DELAY * (2 ** (attempt - 1))
                + random.uniform(0, 1),
                MAX_RETRY_DELAY,
            )

            logger.warning(
                "Temporary Gemini API failure "
                "status_code=%s attempt=%s/%s "
                "retrying_in=%.2fs",
                status_code,
                attempt,
                MAX_ATTEMPTS,
                delay,
            )

            time.sleep(delay)


def embed_code(code: str, file_path: str) -> list[float]:
    """
    Generate a semantic embedding for a source-code chunk.
    """

    text = (
        "Represent this source code for semantic code search.\n"
        f"File: {file_path}\n\n"
        f"{code}"
    )

    return generate_embedding(text)


def embed_query(query: str) -> list[float]:
    """
    Generate an embedding for a natural-language query.
    """

    text = (
        "Represent this natural-language query "
        "for semantic code search.\n\n"
        f"{query}"
    )

    return generate_embedding(text)