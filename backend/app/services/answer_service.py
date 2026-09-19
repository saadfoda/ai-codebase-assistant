import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai


# Load backend/.env
BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"
load_dotenv(ENV_FILE)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY is not set in backend/.env")

client = genai.Client(api_key=api_key)

MODEL = "gemini-3.6-flash"


def generate_answer(query: str, search_results) -> str:
    """
    Generate an answer using the user's question and
    the code chunks retrieved from the repository.
    """

    context_parts = []

    for chunk, distance in search_results:
        context_parts.append(
            f"""
File: {chunk.file_path}
Lines: {chunk.start_line}-{chunk.end_line}

{chunk.content}
"""
        )

    context = "\n---\n".join(context_parts)

    prompt = f"""
You are an AI codebase assistant.

Answer the user's question using ONLY the provided code context.

Rules:
- Do not invent code or files.
- Explain which file(s) are relevant.
- Include line ranges when available.
- If the provided context does not contain enough information to answer,
  say that clearly.
- Keep the explanation concise but useful.

User question:
{query}

Retrieved code context:
{context}
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
    )

    if not response.text:
        raise RuntimeError("Gemini returned an empty response")

    return response.text