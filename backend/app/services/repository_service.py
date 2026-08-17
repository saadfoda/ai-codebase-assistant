import subprocess
from pathlib import Path
from urllib.parse import urlparse


def clone_repository(repository_url: str, destination: str) -> str:
    """
    Clone a GitHub repository into the specified destination.
    """

    destination_path = Path(destination)

    if destination_path.exists():
        raise ValueError("Destination directory already exists.")

    parsed_url = urlparse(repository_url)

    if parsed_url.hostname != "github.com":
        raise ValueError("Only GitHub repositories are supported.")

    subprocess.run(
        [
            "git",
            "clone",
            repository_url,
            str(destination_path),
        ],
        check=True,
    )

    return str(destination_path)