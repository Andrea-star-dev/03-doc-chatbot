from __future__ import annotations

import pytest

from app.llm import AnthropicLLMClient, MockLLMClient, resolve_llm_client


def test_resolve_llm_client_defaults_to_anthropic(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    client = resolve_llm_client()
    assert isinstance(client, AnthropicLLMClient)


def test_resolve_llm_client_returns_mock_when_requested():
    client = resolve_llm_client(provider="mock")
    assert isinstance(client, MockLLMClient)


def test_resolve_llm_client_rejects_unknown_provider():
    with pytest.raises(ValueError):
        resolve_llm_client(provider="unknown-provider")


def test_anthropic_client_construction_does_not_require_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    # API 키가 없어도 객체 생성 자체는 에러가 나면 안 된다 (실제 호출 시에만 에러).
    client = AnthropicLLMClient()
    assert client is not None


def test_mock_llm_client_cites_first_context_block():
    client = MockLLMClient()
    user_prompt = (
        "문맥:\n"
        "[policy.pdf - 2페이지]\n"
        "원격근무는 주 3일까지 신청할 수 있다. 팀장 승인이 필요하다.\n\n"
        "질문: 원격근무는 며칠까지 가능한가요?\n\n"
        "문맥에 근거가 있다면..."
    )

    answer = client.generate(system="아무 시스템 프롬프트", user=user_prompt)

    assert "policy.pdf 2페이지" in answer
    assert "원격근무는 주 3일까지 신청할 수 있다." in answer


def test_mock_llm_client_handles_prompt_without_context_blocks():
    client = MockLLMClient()
    answer = client.generate(system="시스템", user="문맥 블록이 없는 임의의 프롬프트")
    assert "mock" in answer.lower()
