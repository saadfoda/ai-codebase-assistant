
import subprocess
from unittest.mock import patch

import pytest

from app.services.repository_service import (
    clone_repository,
    CLONE_TIMEOUT_SECONDS,
)


VALID_URL = "https://github.com/saadfoda/AlbertaLakesSite"


def test_clone_repository_success(tmp_path):
    destination = tmp_path / "repository"

    with patch(
        "app.services.repository_service.subprocess.run"
    ) as mock_run:

        result = clone_repository(
            VALID_URL,
            str(destination),
        )

        assert result == str(destination)

        mock_run.assert_called_once_with(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--",
                VALID_URL,
                str(destination),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=CLONE_TIMEOUT_SECONDS,
        )


@pytest.mark.parametrize(
    "invalid_url",
    [
        "https://gitlab.com/user/repository",
        "http://github.com/user/repository",
        "https://user:password@github.com/user/repository",
        "https://github.com:8080/user/repository",
        "https://github.com.example.com/user/repository",
    ],
)
def test_clone_repository_invalid_url(tmp_path, invalid_url):
    with patch(
        "app.services.repository_service.subprocess.run"
    ) as mock_run:
        with pytest.raises(ValueError):
            clone_repository(
                invalid_url,
                str(tmp_path / "repository"),
            )

        mock_run.assert_not_called()


def test_clone_repository_existing_destination(tmp_path):
    destination = tmp_path / "repository"
    destination.mkdir()

    with pytest.raises(
        ValueError,
        match="Destination directory already exists",
    ):
        clone_repository(
            VALID_URL,
            str(destination),
        )


def test_clone_repository_timeout(tmp_path):
    with patch(
        "app.services.repository_service.subprocess.run"
    ) as mock_run:

        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd="git clone",
            timeout=CLONE_TIMEOUT_SECONDS,
        )

        with pytest.raises(
            RuntimeError,
            match="Repository cloning timed out",
        ):
            clone_repository(
                VALID_URL,
                str(tmp_path / "repository"),
            )


def test_clone_repository_failure(tmp_path):
    with patch(
        "app.services.repository_service.subprocess.run"
    ) as mock_run:

        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=128,
            cmd="git clone",
        )

        with pytest.raises(
            RuntimeError,
            match="Unable to clone repository",
        ):
            clone_repository(
                VALID_URL,
                str(tmp_path / "repository"),
            )
