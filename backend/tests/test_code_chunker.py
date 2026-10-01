from app.services.code_chunker import chunk_code


def test_chunk_code_splits_large_file():
    content = "\n".join(f"line {i}" for i in range(1, 11))

    chunks = chunk_code(
        content=content,
        file_path="example.py",
        chunk_size=4,
        overlap=1,
    )

    assert len(chunks) == 3

    assert chunks[0]["start_line"] == 1
    assert chunks[0]["end_line"] == 4

    assert chunks[1]["start_line"] == 4
    assert chunks[1]["end_line"] == 7

    assert chunks[2]["start_line"] == 7
    assert chunks[2]["end_line"] == 10


def test_chunk_code_preserves_file_path():
    chunks = chunk_code(
        content="print('hello')",
        file_path="src/example.py",
    )

    assert len(chunks) == 1
    assert chunks[0]["file_path"] == "src/example.py"


def test_empty_file_creates_no_chunks():
    chunks = chunk_code(
        content="",
        file_path="empty.py",
    )

    assert chunks == []
