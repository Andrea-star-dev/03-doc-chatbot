"""질문 → 관련 청크 검색 → LLM 호출. 근거가 없으면 LLM을 부르지 않고 바로
"모른다"로 답한다.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.llm import LLMClient
from app.vectorstore import VectorStore

NO_CONTEXT_ANSWER = "업로드된 문서에서 관련 내용을 찾지 못해 답변할 수 없습니다."

SYSTEM_PROMPT = (
    "당신은 업로드된 사내 문서를 근거로만 질문에 답하는 도우미입니다. "
    "아래 제공되는 문맥(context)에 있는 내용만 사용해서 답하세요. "
    "문맥에 답이 없거나 확신할 수 없으면 추측하지 말고, 반드시 다음 문장으로만 답하세요: "
    f'"{NO_CONTEXT_ANSWER}"'
)


@dataclass(frozen=True)
class Source:
    doc_id: str
    filename: str
    page: int


@dataclass(frozen=True)
class AnswerResult:
    answer: str
    sources: list[Source]
    used_context: bool


def answer_question(
    vector_store: VectorStore,
    llm_client: LLMClient,
    question: str,
    n_results: int = 4,
) -> AnswerResult:
    if vector_store.count() == 0:
        return AnswerResult(answer=NO_CONTEXT_ANSWER, sources=[], used_context=False)

    matches = vector_store.query(question, n_results=n_results)
    if not matches:
        return AnswerResult(answer=NO_CONTEXT_ANSWER, sources=[], used_context=False)

    context_text = "\n\n".join(
        f"[{m['filename']} - {m['page']}페이지]\n{m['text']}" for m in matches
    )
    user_prompt = (
        f"문맥:\n{context_text}\n\n"
        f"질문: {question}\n\n"
        "문맥에 근거가 있다면, 답변 끝에 참고한 문서명과 페이지를 "
        "괄호로 표시하세요. 예: (정책문서.pdf 3페이지)"
    )

    answer_text = llm_client.generate(SYSTEM_PROMPT, user_prompt)
    sources = [Source(doc_id=m["doc_id"], filename=m["filename"], page=m["page"]) for m in matches]

    return AnswerResult(answer=answer_text, sources=sources, used_context=True)
