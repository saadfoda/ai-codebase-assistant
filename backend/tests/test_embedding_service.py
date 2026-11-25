from types import SimpleNamespace
from unittest.mock import patch

import pytest
from google.genai import errors

from app.services.embedding_service import (
    generate_embedding,
    embed_code,
    embed_query,
    EMBEDDING_DIMENSIONS,
    MAX_ATTEMPTS,
)

MODULE = "app.services.embedding_service"

VALID_EMBEDDING = [0.1] * EMBEDDING_DIMENSIONS


def make_response(values):
    return SimpleNamespace(
        embeddings=[
            SimpleNamespace(values=values)
        ]
    )


def make_api_error(code):
    return errors.APIError(
        code,
        {
            "error": {
                "code": code,
                "message": "Simulated API error",
            }
        },
    )


def test_generate_embedding_success():
    with patch(
        f"{MODULE}.client.models.embed_content",
        return_value=make_response(VALID_EMBEDDING),
    ) as mock_embed:
        result = generate_embedding("test code")

    assert result == VALID_EMBEDDING
    mock_embed.assert_called_once()


def test_generate_embedding_retries_rate_limit():
    with (
        patch(
            f"{MODULE}.client.models.embed_content",
            side_effect=[
                make_api_error(429),
                make_response(VALID_EMBEDDING),
            ],
        ) as mock_embed,
        patch(f"{MODULE}.time.sleep") as mock_sleep,
        patch(
            f"{MODULE}.random.uniform",
            return_value=0,
        ),
    ):
        result = generate_embedding("test code")

    assert result == VALID_EMBEDDING
    assert mock_embed.call_count == 2
    mock_sleep.assert_called_once_with(30)


def test_generate_embedding_exhausts_retries():
    with (
        patch(
            f"{MODULE}.client.models.embed_content",
            side_effect=make_api_error(429),
        ) as mock_embed,
        patch(f"{MODULE}.time.sleep") as mock_sleep,
        patch(
            f"{MODULE}.random.uniform",
            return_value=0,
        ),
    ):
        with pytest.raises(errors.APIError):
            generate_embedding("test code")

    assert mock_embed.call_count == MAX_ATTEMPTS
    assert mock_sleep.call_count == MAX_ATTEMPTS - 1

    delays = [
        call.args[0]
        for call in mock_sleep.call_args_list
    ]

    assert delays == [30, 60, 120]


def test_generate_embedding_does_not_retry_invalid_request():
    with (
        patch(
            f"{MODULE}.client.models.embed_content",
            side_effect=make_api_error(400),
        ) as mock_embed,
        patch(f"{MODULE}.time.sleep") as mock_sleep,
    ):
        with pytest.raises(errors.APIError):
            generate_embedding("test code")

    mock_embed.assert_called_once()
    mock_sleep.assert_not_called()


def test_generate_embedding_retries_server_error():
    with (
        patch(
            f"{MODULE}.client.models.embed_content",
            side_effect=[
                make_api_error(503),
                make_response(VALID_EMBEDDING),
            ],
        ) as mock_embed,
        patch(f"{MODULE}.time.sleep") as mock_sleep,
    ):
        result = generate_embedding("test code")

    assert result == VALID_EMBEDDING
    assert mock_embed.call_count == 2
    mock_sleep.assert_called_once()


def test_generate_embedding_rejects_invalid_dimensions():
    with patch(
        f"{MODULE}.client.models.embed_content",
        return_value=make_response([0.1] * 10),
    ):
        with pytest.raises(
            RuntimeError,
            match="Expected 768 dimensions",
        ):
            generate_embedding("test code")


def test_generate_embedding_rejects_empty_response():
    with patch(
        f"{MODULE}.client.models.embed_content",
        return_value=SimpleNamespace(embeddings=[]),
    ):
        with pytest.raises(
            RuntimeError,
            match="Gemini returned no embedding",
        ):
            generate_embedding("test code")


def test_embed_code_uses_shared_function():
    with patch(
        f"{MODULE}.generate_embedding",
        return_value=VALID_EMBEDDING,
    ) as mock_generate:
        result = embed_code(
            code="print('hello')",
            file_path="main.py",
        )

    assert result == VALID_EMBEDDING

    text = mock_generate.call_args.args[0]

    assert "main.py" in text
    assert "print('hello')" in text


def test_embed_query_uses_shared_function():
    with patch(
        f"{MODULE}.generate_embedding",
        return_value=VALID_EMBEDDING,
    ) as mock_generate:
        result = embed_query("Where is authentication handled?")

    assert result == VALID_EMBEDDING

    text = mock_generate.call_args.args[0]

    assert "Where is authentication handled?" in text