from __future__ import annotations

from app.rag import NO_CONTEXT_ANSWER, answer_question
from app.vectorstore import VectorStore
from tests.fakes import FakeLLMClient, HashEmbeddingFunction


def make_store(tmp_path) -> VectorStore:
    return VectorStore(tmp_path / "chroma", embedding_function=HashEmbeddingFunction())


def test_answer_question_returns_no_context_when_store_is_empty(tmp_path):
    store = make_store(tmp_path)
    llm = FakeLLMClient()

    result = answer_question(store, llm, "원격근무는 며칠까지 가능한가요?")

    assert result.answer == NO_CONTEXT_ANSWER
    assert result.used_context is False
    assert result.sources == []
    assert llm.calls == []  # 근거가 없으면 LLM을 부르지 않아야 함


def test_answer_question_calls_llm_with_context_when_relevant_chunks_exist(tmp_path):
    store = make_store(tmp_path)
    store.add_document_chunks(
        "doc-1",
        "policy.pdf",
        [(2, "원격근무는 주 3일까지 신청할 수 있다")],
    )
    llm = FakeLLMClient(response="주 3일까지 가능합니다.")

    result = answer_question(store, llm, "원격근무는 며칠까지 가능한가요?")

    assert result.answer == "주 3일까지 가능합니다."
    assert result.used_context is True
    assert len(result.sources) == 1
    assert result.sources[0].doc_id == "doc-1"
    assert result.sources[0].filename == "policy.pdf"
    assert result.sources[0].page == 2

    assert len(llm.calls) == 1
    system, user = llm.calls[0]
    assert "모른다" in system or NO_CONTEXT_ANSWER in system
    assert "원격근무는 주 3일까지 신청할 수 있다" in user
    assert "원격근무는 며칠까지 가능한가요?" in user


def test_answer_question_respects_n_results(tmp_path):
    store = make_store(tmp_path)
    store.add_document_chunks(
        "doc-1",
        "policy.pdf",
        [(1, "문장 하나"), (2, "문장 둘"), (3, "문장 셋")],
    )
    llm = FakeLLMClient()

    result = answer_question(store, llm, "문장", n_results=2)

    assert len(result.sources) == 2
