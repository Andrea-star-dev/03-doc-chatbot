"""PDF에서 페이지별 텍스트를 뽑고, 임베딩하기 좋은 크기로 청크를 나눈다."""
from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader


def extract_pages(path: str | Path) -> list[str]:
    """PDF 파일의 각 페이지 텍스트를 리스트로 반환한다 (1페이지 = 리스트의 0번째)."""
    reader = PdfReader(str(path))
    return [(page.extract_text() or "").strip() for page in reader.pages]


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """text를 chunk_size(문자 수 기준) 근처로 나눈다. 단어 중간에서 자르지 않고,
    다음 청크는 overlap만큼 이전 청크의 끝부분을 이어받아 맥락이 끊기지 않게 한다.
    """
    if overlap >= chunk_size:
        raise ValueError("overlap은 chunk_size보다 작아야 합니다")

    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    i = 0

    while i < len(words):
        word = words[i]
        added_len = len(word) + (1 if current else 0)

        if current and current_len + added_len > chunk_size:
            chunks.append(" ".join(current))
            overlap_words = _take_overlap(current, overlap)
            # overlap이 이전 청크 전체를 그대로 다시 가져오면 진전이 없으므로 버린다.
            current = [] if overlap_words == current else overlap_words
            current_len = _joined_len(current)
            continue

        current.append(word)
        current_len += added_len
        i += 1

    if current:
        chunks.append(" ".join(current))

    return chunks


def _take_overlap(words: list[str], overlap: int) -> list[str]:
    """words의 끝부분에서 overlap 문자 수만큼(단어 단위로) 가져온다."""
    result: list[str] = []
    length = 0
    for word in reversed(words):
        length += len(word) + (1 if result else 0)
        result.insert(0, word)
        if length >= overlap:
            break
    return result


def _joined_len(words: list[str]) -> int:
    if not words:
        return 0
    return sum(len(w) for w in words) + (len(words) - 1)
