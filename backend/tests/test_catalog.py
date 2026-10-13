from __future__ import annotations

from app import catalog


def test_list_entries_empty_when_no_file(tmp_path):
    path = tmp_path / "catalog.json"
    assert catalog.list_entries(path) == []


def test_add_entry_then_list_and_get(tmp_path):
    path = tmp_path / "catalog.json"
    catalog.add_entry(path, "doc-1", {"filename": "a.pdf", "num_pages": 3})

    entries = catalog.list_entries(path)
    assert entries == [{"doc_id": "doc-1", "filename": "a.pdf", "num_pages": 3}]

    entry = catalog.get_entry(path, "doc-1")
    assert entry == {"doc_id": "doc-1", "filename": "a.pdf", "num_pages": 3}


def test_get_entry_returns_none_for_unknown_doc(tmp_path):
    path = tmp_path / "catalog.json"
    assert catalog.get_entry(path, "unknown") is None


def test_add_entry_persists_across_loads(tmp_path):
    path = tmp_path / "catalog.json"
    catalog.add_entry(path, "doc-1", {"filename": "a.pdf"})
    catalog.add_entry(path, "doc-2", {"filename": "b.pdf"})

    entries = catalog.list_entries(path)
    assert {e["doc_id"] for e in entries} == {"doc-1", "doc-2"}
