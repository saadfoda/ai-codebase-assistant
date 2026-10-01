from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.routes.repositories as repository_routes
from app.database import get_db
from app.models.models import Repository


class FakeQuery:
    def __init__(self, repositories):
        self.repositories = repositories

    def all(self):
        return self.repositories

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def first(self):
        return self.repositories[0] if self.repositories else None


class FakeDB:
    def __init__(self, repositories=None):
        self.repositories = repositories or []

    def query(self, model):
        return FakeQuery(self.repositories)

    def add(self, repository):
        if repository.id is None:
            next_id = (
                max((repo.id for repo in self.repositories), default=0) + 1
            )
            repository.id = next_id

        self.repositories.append(repository)

    def commit(self):
        pass

    def refresh(self, repository):
        pass


@pytest.fixture
def test_client():
    repository = Repository(
        id=1,
        url="https://github.com/example/test-repo",
        name="Test Repository",
        description="Test repository",
    )

    db = FakeDB([repository])

    app = FastAPI()
    app.include_router(repository_routes.router)

    app.dependency_overrides[get_db] = lambda: db

    return TestClient(app), db


def test_list_repositories(test_client):
    client, _ = test_client

    response = client.get("/repositories/")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == 1
    assert data[0]["name"] == "Test Repository"


def test_create_repository_deduplicates_git_suffix(test_client):
    client, db = test_client

    response = client.post(
        "/repositories/",
        json={
            "url": "https://github.com/example/test-repo.git",
            "name": "Duplicate Repository",
            "description": "",
        },
    )

    assert response.status_code == 200

    data = response.json()

    # Should return the existing repository rather than creating another one.
    assert data["id"] == 1
    assert len(db.repositories) == 1


def test_ask_repository(test_client, monkeypatch):
    client, _ = test_client

    fake_chunk = SimpleNamespace(
        file_path="src/example.py",
        start_line=10,
        end_line=20,
        content="def hello():\n    return 'hello'",
    )

    def fake_search_code(db, query, repository_id, limit):
        return [(fake_chunk, 0.15)]

    def fake_generate_answer(query, results):
        return "The function is implemented in src/example.py."

    monkeypatch.setattr(
        repository_routes,
        "search_code",
        fake_search_code,
    )

    monkeypatch.setattr(
        repository_routes,
        "generate_answer",
        fake_generate_answer,
    )

    response = client.get(
        "/repositories/1/ask",
        params={
            "q": "Where is hello implemented?",
            "limit": 5,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["repository_id"] == 1
    assert data["answer"] == (
        "The function is implemented in src/example.py."
    )
    assert data["sources"][0]["file_path"] == "src/example.py"
    assert data["sources"][0]["start_line"] == 10
    assert data["sources"][0]["end_line"] == 20


def test_ingest_repository(test_client, monkeypatch):
    client, _ = test_client

    def fake_ingest_repository(db, repository_id, repository_url):
        return {
            "repository_id": repository_id,
            "repository_path": "test/repository",
            "files_processed": 5,
            "chunks_created": 10,
            "chunks_embedded": 10,
        }

    monkeypatch.setattr(
        repository_routes,
        "ingest_repository",
        fake_ingest_repository,
    )

    response = client.post("/repositories/1/ingest")

    assert response.status_code == 200

    data = response.json()

    assert data["repository_id"] == 1
    assert data["files_processed"] == 5
    assert data["chunks_created"] == 10
    assert data["chunks_embedded"] == 10
