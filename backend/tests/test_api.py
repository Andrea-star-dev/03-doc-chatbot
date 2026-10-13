from __future__ import annotations

from scripts.generate_sample_pdf import generate, generate_blank


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_list_documents_empty_initially(client):
    resp = client.get("/documents")
    assert resp.status_code == 200
    assert resp.json() == []


def test_upload_pdf_then_appears_in_list(client, tmp_path):
    pdf_path = generate(tmp_path / "sample.pdf")

    with pdf_path.open("rb") as f:
        resp = client.post(
            "/documents",
            files={"file": ("remote_work_policy.pdf", f, "application/pdf")},
        )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["filename"] == "remote_work_policy.pdf"
    assert body["num_pages"] == 3
    assert body["num_chunks"] > 0
    doc_id = body["doc_id"]

    listed = client.get("/documents").json()
    assert len(listed) == 1
    assert listed[0]["doc_id"] == doc_id
    assert listed[0]["filename"] == "remote_work_policy.pdf"


def test_upload_rejects_non_pdf(client):
    resp = client.post(
        "/documents",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert resp.status_code == 400


def test_query_rejects_empty_question(client):
    resp = client.post("/query", json={"question": "   "})
    assert resp.status_code == 400


def test_query_returns_no_context_when_no_documents_uploaded(client, llm_client):
    resp = client.post("/query", json={"question": "원격근무는 며칠까지 가능한가요?"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["used_context"] is False
    assert body["sources"] == []
    assert llm_client.calls == []


def test_query_after_upload_returns_answer_with_sources(client, llm_client, tmp_path):
    llm_client.response = "주 3일까지 원격근무를 신청할 수 있습니다."
    pdf_path = generate(tmp_path / "sample.pdf")

    with pdf_path.open("rb") as f:
        upload = client.post(
            "/documents",
            files={"file": ("remote_work_policy.pdf", f, "application/pdf")},
        )
    doc_id = upload.json()["doc_id"]

    resp = client.post("/query", json={"question": "원격근무 신청은 언제까지 해야 하나요?"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"] == "주 3일까지 원격근무를 신청할 수 있습니다."
    assert body["used_context"] is True
    assert body["sources"]
    assert all(s["doc_id"] == doc_id for s in body["sources"])
    assert len(llm_client.calls) == 1


def test_upload_rejects_pdf_with_no_extractable_text(client, tmp_path):
    pdf_path = generate_blank(tmp_path / "blank.pdf")

    with pdf_path.open("rb") as f:
        resp = client.post(
            "/documents",
            files={"file": ("scanned.pdf", f, "application/pdf")},
        )

    assert resp.status_code == 400
    assert client.get("/documents").json() == []
