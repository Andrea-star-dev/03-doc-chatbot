from __future__ import annotations

from app.vectorstore import VectorStore
from tests.fakes import HashEmbeddingFunction


def make_store(tmp_path):
    return VectorStore(tmp_path / "chroma", embedding_function=HashEmbeddingFunction())


def test_add_document_chunks_returns_count(tmp_path):
    store = make_store(tmp_path)
    chunks = [(1, "원격근무 신청은 2일 전까지"), (1, "팀장 승인이 필요하다")]

    added = store.add_document_chunks("doc-1", "policy.pdf", chunks)

    assert added == 2
    assert store.count() == 2


def test_add_document_chunks_with_empty_list_returns_zero(tmp_path):
    store = make_store(tmp_path)
    assert store.add_document_chunks("doc-1", "policy.pdf", []) == 0
    assert store.count() == 0


def test_query_returns_most_relevant_chunk_first(tmp_path):
    store = make_store(tmp_path)
    store.add_document_chunks(
        "doc-1",
        "policy.pdf",
        [
            (1, "원격근무 신청 절차는 희망일 2일 전까지 인사 시스템에 등록한다"),
            (2, "공용 와이파이 사용 시 반드시 VPN을 통해 접속해야 한다"),
            (3, "점심시간은 낮 12시부터 1시까지이다"),
        ],
    )

    results = store.query("원격근무 신청 절차가 어떻게 되나요", n_results=3)

    assert results
    assert results[0]["page"] == 1
    assert results[0]["doc_id"] == "doc-1"
    assert results[0]["filename"] == "policy.pdf"


def test_delete_document_removes_only_that_document(tmp_path):
    store = make_store(tmp_path)
    store.add_document_chunks("doc-1", "a.pdf", [(1, "문서 A의 내용")])
    store.add_document_chunks("doc-2", "b.pdf", [(1, "문서 B의 내용")])

    store.delete_document("doc-1")

    assert store.count() == 1
    remaining = store.query("문서", n_results=10)
    assert all(r["doc_id"] == "doc-2" for r in remaining)
