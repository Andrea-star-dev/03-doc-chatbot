"""테스트 전용 가짜 임베딩 함수. 네트워크/모델 다운로드 없이 결정적으로 동작한다.

단어 해싱(bag-of-words hashing trick) 방식이라 실제 의미 이해는 못 하지만,
같은 단어를 공유하는 텍스트끼리는 비슷한 벡터가 나오므로 검색 테스트에는 충분하다.
"""
from __future__ import annotations

import hashlib
import math


class HashEmbeddingFunction:
    # dim=64였을 때 CI에서 서로 다른 두 테스트 문장이 우연히 정확히 같은 코사인
    # 유사도로 해시 충돌해서, 어느 쪽이 1등인지가 환경마다 달라지는 flaky 테스트가
    # 났었다 (로컬은 우연히 통과, GitHub Actions에서는 실패). 차원을 키워 짧은
    # 테스트 문장 몇 개 수준에서는 충돌이 사실상 나지 않게 한다.
    def __init__(self, dim: int = 256) -> None:
        self._dim = dim

    def is_legacy(self) -> bool:
        return False

    def __call__(self, input: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in input]

    def embed_query(self, input: list[str]) -> list[list[float]]:
        return self(input)

    @staticmethod
    def name() -> str:
        return "test-hash-embedding"

    def _embed(self, text: str) -> list[float]:
        vec = [0.0] * self._dim
        for token in text.lower().split():
            idx = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % self._dim
            vec[idx] += 1.0

        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]


class FakeLLMClient:
    """실제 API를 부르지 않는 가짜 LLM. 호출 기록을 남겨 테스트에서 검증할 수 있다."""

    def __init__(self, response: str = "테스트용 고정 답변입니다.") -> None:
        self.response = response
        self.calls: list[tuple[str, str]] = []

    def generate(self, system: str, user: str) -> str:
        self.calls.append((system, user))
        return self.response
