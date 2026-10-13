from __future__ import annotations

import pytest

from app.pdf_processing import chunk_text, extract_pages
from scripts.generate_sample_pdf import generate, generate_blank


def test_extract_pages_returns_text_per_page(tmp_path):
    pdf_path = generate(tmp_path / "sample.pdf")

    pages = extract_pages(pdf_path)

    assert len(pages) == 3
    assert "원격근무 규정" in pages[0]
    assert "신청 절차" in pages[1]
    assert "장비 및 보안" in pages[2]


def test_extract_pages_blank_pdf_returns_empty_strings(tmp_path):
    pdf_path = generate_blank(tmp_path / "blank.pdf")

    pages = extract_pages(pdf_path)

    assert len(pages) == 1
    assert pages[0] == ""


def test_chunk_text_returns_whole_text_when_short():
    text = "짧은 문장 하나"
    chunks = chunk_text(text, chunk_size=100, overlap=10)
    assert chunks == [text]


def test_chunk_text_splits_long_text_without_breaking_words():
    words = [f"단어{i}" for i in range(50)]
    text = " ".join(words)

    chunks = chunk_text(text, chunk_size=30, overlap=10)

    assert len(chunks) > 1
    for chunk in chunks:
        for word in chunk.split():
            assert word in words  # 단어가 중간에서 잘리지 않았어야 함


def test_chunk_text_consecutive_chunks_overlap():
    words = [f"단어{i}" for i in range(50)]
    text = " ".join(words)

    chunks = chunk_text(text, chunk_size=30, overlap=10)

    first_words = chunks[0].split()
    second_words = chunks[1].split()
    shared = set(first_words) & set(second_words)
    assert shared, "연속된 청크 사이에 겹치는 단어가 있어야 함 (overlap)"


def test_chunk_text_empty_string_returns_no_chunks():
    assert chunk_text("", chunk_size=100, overlap=10) == []
    assert chunk_text("   ", chunk_size=100, overlap=10) == []


def test_chunk_text_rejects_overlap_not_smaller_than_chunk_size():
    with pytest.raises(ValueError):
        chunk_text("아무 텍스트", chunk_size=50, overlap=50)


def test_chunk_text_handles_single_word_longer_than_chunk_size():
    huge_word = "a" * 500
    text = f"{huge_word} 그 다음 단어들 몇 개 더"

    chunks = chunk_text(text, chunk_size=50, overlap=10)

    assert chunks  # 무한 루프 없이 끝까지 처리돼야 함
    assert huge_word in chunks[0]
