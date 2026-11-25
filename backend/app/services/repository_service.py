
import logging
import subprocess
from pathlib import Path
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

CLONE_TIMEOUT_SECONDS = 120


def clone_repository(repository_url: str, destination: str) -> str:
    """
    Clone a public GitHub repository with validation,
    timeout protection, and application logging.
    """

    destination_path = Path(destination)

    if destination_path.exists():
        raise ValueError("Destination directory already exists.")

    parsed_url = urlparse(repository_url)

    if (
        parsed_url.scheme != "https"
        or parsed_url.hostname != "github.com"
        or parsed_url.username is not None
        or parsed_url.password is not None
        or parsed_url.port is not None
    ):
        raise ValueError(
            "Only HTTPS GitHub repository URLs are supported."
        )

    logger.info("Starting GitHub repository clone")

    try:
        subprocess.run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--",
                repository_url,
                str(destination_path),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=CLONE_TIMEOUT_SECONDS,
        )

    except subprocess.TimeoutExpired as exc:
        logger.error("Repository clone timed out")
        raise RuntimeError("Repository cloning timed out.") from exc

    except subprocess.CalledProcessError as exc:
        logger.error(
            "Repository clone failed with exit code %s",
            exc.returncode,
        )
        raise RuntimeError("Unable to clone repository.") from exc

    logger.info("Repository cloned successfully")

    return str(destination_path)
