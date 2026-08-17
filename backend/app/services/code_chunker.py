from pathlib import Path


def chunk_code(
    content: str,
    file_path: str,
    chunk_size: int = 80,
    overlap: int = 10,
) -> list[dict]:
    """
    Split source code into overlapping chunks.

    Args:
        content: Source code contents.
        file_path: Relative path of the source file.
        chunk_size: Number of lines per chunk.
        overlap: Number of overlapping lines between chunks.

    Returns:
        A list of code chunks with metadata.
    """

    lines = content.splitlines()

    chunks = []

    start = 0
    chunk_index = 0

    while start < len(lines):
        end = min(start + chunk_size, len(lines))

        chunk_content = "\n".join(lines[start:end])

        chunks.append(
            {
                "file_path": file_path,
                "chunk_index": chunk_index,
                "start_line": start + 1,
                "end_line": end,
                "content": chunk_content,
            }
        )

        if end == len(lines):
            break

        start = end - overlap
        chunk_index += 1

    return chunks