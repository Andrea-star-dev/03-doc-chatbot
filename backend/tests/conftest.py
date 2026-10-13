from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from tests.fakes import HashEmbeddingFunction


@pytest.fixture
def settings(tmp_path) -> Settings:
    data_dir = tmp_path / "data"
    return Settings(
        data_dir=data_dir,
        uploads_dir=data_dir / "uploads",
        chroma_dir=data_dir / "chroma",
        catalog_path=data_dir / "catalog.json",
        chunk_size=200,
        chunk_overlap=40,
    )


@pytest.fixture
def embedding_function() -> HashEmbeddingFunction:
    return HashEmbeddingFunction()


@pytest.fixture
def client(settings, embedding_function) -> TestClient:
    app = create_app(settings=settings, embedding_function=embedding_function)
    return TestClient(app)
