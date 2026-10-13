"""질문에 답을 생성하는 LLM 클라이언트. 기본은 Anthropic이고, LLMClient 프로토콜을
구현하는 다른 클라이언트로 쉽게 바꿀 수 있다 (예: OpenAI, 로컬 모델 등).
"""
from __future__ import annotations

import os
import re
from typing import Protocol

DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-5-5"


class LLMClient(Protocol):
    def generate(self, system: str, user: str) -> str: ...


class AnthropicLLMClient:
    """Anthropic API로 답을 생성한다. ANTHROPIC_API_KEY가 없으면 생성 시점이 아니라
    실제로 질문할 때(generate 호출 시) 에러가 난다.
    """

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self._api_key = api_key
        self._model = model or os.environ.get("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL)
        self._client = None  # 실제 호출 시점에 생성 (지연 초기화)

    def generate(self, system: str, user: str) -> str:
        if self._client is None:
            import anthropic  # 테스트 등에서 이 클래스를 안 쓰면 import 비용도 안 든다.

            self._client = anthropic.Anthropic(api_key=self._api_key)

        response = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(block.text for block in response.content if block.type == "text")


_CONTEXT_BLOCK_RE = re.compile(r"\[([^\]]+) - (\d+)페이지\]\n(.*?)(?=\n\n\[|\n\n질문:|\Z)", re.S)


def _first_sentence(text: str, max_len: int = 80) -> str:
    text = text.strip()
    for sep in ("다.", ".", "!", "?"):
        idx = text.find(sep)
        if 0 < idx <= max_len:
            return text[: idx + len(sep)]
    return text[:max_len] + ("..." if len(text) > max_len else "")


class MockLLMClient:
    """실제 API를 호출하지 않고, 전달된 문맥에서 그럴듯한 답을 만들어내는 클라이언트.

    API 키 없이 오프라인으로 개발하거나, 데모/스크린샷을 찍을 때 쓴다.
    LLM_PROVIDER=mock 으로 켠다. 문맥이 전혀 전달되지 않았으면
    (= rag.answer_question이 LLM을 부를 필요가 없다고 판단한 경우) 이 클래스까지
    호출이 오지 않으므로, 여기서는 항상 문맥이 있다고 가정해도 된다.
    """

    def generate(self, system: str, user: str) -> str:
        blocks = _CONTEXT_BLOCK_RE.findall(user)
        if not blocks:
            return "문맥을 해석하지 못해 답변할 수 없습니다. (mock)"

        filename, page, text = blocks[0]
        snippet = _first_sentence(text)
        return f'문서 내용에 따르면 "{snippet}" ({filename} {page}페이지)'


def resolve_llm_client(provider: str | None = None) -> LLMClient:
    """LLM_PROVIDER 환경변수(기본 anthropic)로 어떤 클라이언트를 쓸지 고른다.
    다른 공급자를 추가하려면 LLMClient를 구현하고 여기에 분기를 추가하면 된다.
    """
    provider = provider or os.environ.get("LLM_PROVIDER", "anthropic")
    if provider == "anthropic":
        return AnthropicLLMClient()
    if provider == "mock":
        return MockLLMClient()
    raise ValueError(
        f"지원하지 않는 LLM_PROVIDER: {provider!r} (현재는 'anthropic', 'mock' 지원)"
    )
