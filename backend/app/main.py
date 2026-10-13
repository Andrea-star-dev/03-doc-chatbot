"""FastAPI 앱: PDF 업로드 → 텍스트 추출/청킹 → Chroma 저장.

(질의응답 엔드포인트는 Day 2에서 추가된다.)
"""
from __future__ import annotations

import shutil
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

from app import catalog
from app.config import Settings, load_settings
from app.llm import LLMClient, resolve_llm_client
from app.pdf_processing import chunk_text, extract_pages
from app.rag import answer_question
from app.vectorstore import VectorStore


class QueryRequest(BaseModel):
    question: str
    n_results: int = 4


def create_app(
    settings: Settings | None = None,
    embedding_function: Any | None = None,
    llm_client: LLMClient | None = None,
) -> FastAPI:
    settings = settings or load_settings()
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    settings.chroma_dir.mkdir(parents=True, exist_ok=True)

    vector_store = VectorStore(settings.chroma_dir, embedding_function=embedding_function)
    llm_client = llm_client or resolve_llm_client()

    app = FastAPI(title="사내 문서 검색 챗봇 API")
    app.state.settings = settings
    app.state.vector_store = vector_store
    app.state.llm_client = llm_client

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

    @app.post("/query")
    def query(payload: QueryRequest) -> dict[str, Any]:
        if not payload.question.strip():
            raise HTTPException(status_code=400, detail="question이 비어있습니다.")

        try:
            result = answer_question(
                vector_store, llm_client, payload.question, n_results=payload.n_results
            )
        except Exception as exc:  # noqa: BLE001 - LLM 호출 실패를 그대로 502로 전달
            raise HTTPException(status_code=502, detail=f"답변 생성 실패: {exc}") from exc

        return {
            "answer": result.answer,
            "used_context": result.used_context,
            "sources": [
                {"doc_id": s.doc_id, "filename": s.filename, "page": s.page}
                for s in result.sources
            ],
        }

    return app


app = create_app()
