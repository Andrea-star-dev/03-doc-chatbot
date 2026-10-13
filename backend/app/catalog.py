"""업로드된 문서 목록(파일명, 페이지 수, 청크 수 등)을 JSON 파일 하나로 관리한다."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, data: dict[str, dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_entry(path: Path, doc_id: str, record: dict[str, Any]) -> None:
    data = _load(path)
    data[doc_id] = record
    _save(path, data)


def list_entries(path: Path) -> list[dict[str, Any]]:
    data = _load(path)
    return [{"doc_id": doc_id, **record} for doc_id, record in data.items()]


def get_entry(path: Path, doc_id: str) -> dict[str, Any] | None:
    data = _load(path)
    record = data.get(doc_id)
    if record is None:
        return None
    return {"doc_id": doc_id, **record}
