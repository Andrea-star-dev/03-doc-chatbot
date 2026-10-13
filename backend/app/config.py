"""환경변수 기반 설정. 전부 기본값이 있어 아무 설정 없이도 바로 동작한다."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    uploads_dir: Path
    chroma_dir: Path
    catalog_path: Path
    chunk_size: int
    chunk_overlap: int


def load_settings() -> Settings:
    data_dir = Path(os.environ.get("DOC_CHATBOT_DATA_DIR", BASE_DIR / "data"))
    return Settings(
        data_dir=data_dir,
        uploads_dir=data_dir / "uploads",
        chroma_dir=data_dir / "chroma",
        catalog_path=data_dir / "catalog.json",
        chunk_size=int(os.environ.get("DOC_CHATBOT_CHUNK_SIZE", "800")),
        chunk_overlap=int(os.environ.get("DOC_CHATBOT_CHUNK_OVERLAP", "100")),
    )
