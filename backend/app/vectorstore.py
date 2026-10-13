"""문서 청크를 Chroma(로컬 벡터 DB)에 저장하고 검색한다."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import chromadb

COLLECTION_NAME = "documents"


class VectorStore:
    """Chroma 컬렉션 하나를 감싼 얇은 래퍼.

    embedding_function을 넘기지 않으면 Chroma의 기본 임베딩 모델을 사용한다
    (최초 호출 시 모델을 한 번 내려받는다). 테스트에서는 네트워크 없이 동작하는
    가짜 임베딩 함수를 주입한다.
    """

    def __init__(
        self,
        persist_dir: str | Path,
        embedding_function: Any | None = None,
        collection_name: str = COLLECTION_NAME,
    ) -> None:
        self._client = chromadb.PersistentClient(path=str(persist_dir))
        kwargs: dict[str, Any] = {}
        if embedding_function is not None:
            kwargs["embedding_function"] = embedding_function
        self._collection = self._client.get_or_create_collection(name=collection_name, **kwargs)

    def add_document_chunks(self, doc_id: str, filename: str, chunks: list[tuple[int, str]]) -> int:
        """chunks는 (page_number, chunk_text) 리스트. 저장한 청크 개수를 반환한다."""
        if not chunks:
            return 0

        ids = [f"{doc_id}-{page}-{idx}" for idx, (page, _) in enumerate(chunks)]
        documents = [text for _, text in chunks]
        metadatas = [{"doc_id": doc_id, "filename": filename, "page": page} for page, _ in chunks]

        self._collection.add(ids=ids, documents=documents, metadatas=metadatas)
        return len(ids)

    def query(self, query_text: str, n_results: int = 5) -> list[dict[str, Any]]:
        """query_text와 가장 비슷한 청크들을 (거리가 가까운 순으로) 반환한다."""
        result = self._collection.query(query_texts=[query_text], n_results=n_results)

        ids = result.get("ids", [[]])[0]
        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        dists = result.get("distances", [[]])[0]

        matches = []
        for chunk_id, doc, meta, dist in zip(ids, docs, metas, dists):
            matches.append({"id": chunk_id, "text": doc, "distance": dist, **(meta or {})})
        return matches

    def count(self) -> int:
        return self._collection.count()

    def delete_document(self, doc_id: str) -> None:
        self._collection.delete(where={"doc_id": doc_id})
