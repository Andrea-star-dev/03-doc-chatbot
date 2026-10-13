"""질문에 답을 생성하는 LLM 클라이언트. 기본은 Anthropic이고, LLMClient 프로토콜을
구현하는 다른 클라이언트로 쉽게 바꿀 수 있다 (예: OpenAI, 로컬 모델 등).
"""
from __future__ import annotations

import os
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


def resolve_llm_client(provider: str | None = None) -> LLMClient:
    """LLM_PROVIDER 환경변수(기본 anthropic)로 어떤 클라이언트를 쓸지 고른다.
    다른 공급자를 추가하려면 LLMClient를 구현하고 여기에 분기를 추가하면 된다.
    """
    provider = provider or os.environ.get("LLM_PROVIDER", "anthropic")
    if provider == "anthropic":
        return AnthropicLLMClient()
    raise ValueError(f"지원하지 않는 LLM_PROVIDER: {provider!r} (현재는 'anthropic'만 지원)")
