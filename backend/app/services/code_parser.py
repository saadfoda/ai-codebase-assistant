from pathlib import Path


SUPPORTED_EXTENSIONS = {
    ".py",
    ".java",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".cs",
    ".cpp",
    ".c",
    ".h",
    ".hpp",
}


IGNORED_DIRECTORIES = {
    ".git",
    ".idea",
    "node_modules",
    ".venv",
    "venv",
    "build",
    "dist",
    "target",
    "__pycache__",
}


def scan_repository(repository_path: str) -> list[dict]:
    """
    Scan a cloned repository and return supported source files.
    """

    root = Path(repository_path)

    if not root.exists():
        raise FileNotFoundError(
            f"Repository path does not exist: {repository_path}"
        )

    files = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        if any(directory in IGNORED_DIRECTORIES for directory in path.parts):
            continue

        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        files.append(
            {
                "path": str(path.relative_to(root)),
                "extension": path.suffix.lower(),
            }
        )

    return files

def read_source_file(repository_path: str, relative_path: str) -> str:
    root = Path(repository_path)
    file_path = root / relative_path

    if not file_path.exists():
        raise FileNotFoundError(
            f"Source file does not exist: {relative_path}"
        )

    return file_path.read_text(encoding="utf-8")

def read_repository_files(repository_path: str) -> list[dict]:
    """
    Read all supported source files in a repository.
    """

    files = scan_repository(repository_path)
    results = []

    for file in files:
        content = read_source_file(repository_path, file["path"])

        results.append(
            {
                "path": file["path"],
                "extension": file["extension"],
                "content": content,
            }
        )

    return results