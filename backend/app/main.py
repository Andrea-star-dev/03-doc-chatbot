"""FastAPI 앱: PDF 업로드 → 텍스트 추출/청킹 → Chroma 저장.

(질의응답 엔드포인트는 Day 2에서 추가된다.)
"""
from __future__ import annotations

import shutil
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile

from app import catalog
from app.config import Settings, load_settings
from app.pdf_processing import chunk_text, extract_pages
from app.vectorstore import VectorStore


def create_app(settings: Settings | None = None, embedding_function: Any | None = None) -> FastAPI:
    settings = settings or load_settings()
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    settings.chroma_dir.mkdir(parents=True, exist_ok=True)

    vector_store = VectorStore(settings.chroma_dir, embedding_function=embedding_function)

    app = FastAPI(title="사내 문서 검색 챗봇 API")
    app.state.settings = settings
    app.state.vector_store = vector_store

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/documents")
    def upload_document(file: UploadFile = File(...)) -> dict[str, Any]:
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="PDF 파일만 업로드할 수 있습니다.")

        doc_id = uuid.uuid4().hex[:12]
        dest_path = settings.uploads_dir / f"{doc_id}.pdf"
        with dest_path.open("wb") as out:
            shutil.copyfileobj(file.file, out)

        pages = extract_pages(dest_path)
        if not any(page.strip() for page in pages):
            dest_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=400,
                detail="PDF에서 텍스트를 추출할 수 없습니다 (스캔 이미지 PDF는 아직 지원하지 않음).",
            )

        chunk_records: list[tuple[int, str]] = [
            (page_num, chunk)
            for page_num, page_text in enumerate(pages, start=1)
            for chunk in chunk_text(page_text, settings.chunk_size, settings.chunk_overlap)
        ]

        num_chunks = vector_store.add_document_chunks(doc_id, file.filename, chunk_records)

        record = {
            "filename": file.filename,
            "num_pages": len(pages),
            "num_chunks": num_chunks,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        }
        catalog.add_entry(settings.catalog_path, doc_id, record)

        return {"doc_id": doc_id, **record}

    @app.get("/documents")
    def list_documents() -> list[dict[str, Any]]:
        return catalog.list_entries(settings.catalog_path)

    return app


app = create_app()
