from __future__ import annotations

import pytest

from app.llm import AnthropicLLMClient, resolve_llm_client


def test_resolve_llm_client_defaults_to_anthropic(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    client = resolve_llm_client()
    assert isinstance(client, AnthropicLLMClient)


def test_resolve_llm_client_rejects_unknown_provider():
    with pytest.raises(ValueError):
        resolve_llm_client(provider="unknown-provider")


def test_anthropic_client_construction_does_not_require_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    # API 키가 없어도 객체 생성 자체는 에러가 나면 안 된다 (실제 호출 시에만 에러).
    client = AnthropicLLMClient()
    assert client is not None
