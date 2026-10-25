"""GT-4: the one-page UI and the documents-list endpoint behind it.

Covers: GET / serves the page with its key structural elements, the
static assets are served, GET /api/v1/documents lists what uploads
stored (and 503s when unconfigured), and the page's JavaScript renders
document-derived text only via textContent — uploaded documents are
untrusted input, so an HTML-string rendering path in app.js would be
an XSS hole. The JS check is structural: the shipped file is scanned
for the forbidden API, which is a guarantee about the code as written,
not about any single payload.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import groundtruth.api
from groundtruth.api.app import app, get_embedding_provider, get_session_factory
from groundtruth.evidence.db import Base

# --------------------------------------------------------------------------
# Helpers (same minimal-PDF + fake-provider pattern as test_gt1_persistence)
# --------------------------------------------------------------------------


def make_pdf_bytes(pages: list[list[str]]) -> bytes:
    def escape(text: str) -> str:
        return text.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")

    objects: list[bytes] = []
    page_obj_numbers: list[int] = []
    content_obj_numbers: list[int] = []
    next_number = 3
    for lines in pages:
        page_obj_numbers.append(next_number)
        content_obj_numbers.append(next_number + 1)
        next_number += 2
    font_number = next_number

    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    kids_ref = " ".join(f"{n} 0 R" for n in page_obj_numbers)
    objects.append(f"<< /Type /Pages /Kids [{kids_ref}] /Count {len(pages)} >>".encode())
    for lines, page_no, content_no in zip(
        pages, page_obj_numbers, content_obj_numbers, strict=True
    ):
        objects.append(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                f"/Contents {content_no} 0 R /Resources << /Font << /F1 {font_number} 0 R >> >> >>"
            ).encode()
        )
        stream_lines = ["BT", "/F1 12 Tf", "14 TL", "72 720 Td"]
        for index, line in enumerate(lines):
            if index:
                stream_lines.append("T*")
            stream_lines.append(f"({escape(line)}) Tj")
        stream_lines.append("ET")
        stream = "\n".join(stream_lines).encode()
        objects.append(
            b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream"
        )
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    out = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    xref_start = len(out)
    size = len(objects) + 1
    out += f"xref\n0 {size}\n".encode()
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {size} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF\n".encode()
    return bytes(out)


class FakeEmbeddingProvider:
    provider_name = "fake-provider"
    model_name = "fake-embedding-v1"

    def embed(self, texts):
        vectors = []
        for text in texts:
            digest = sha256(text.encode("utf-8")).digest()
            vectors.append([byte / 255.0 for byte in digest[:8]])
        return vectors


TWO_PAGE_PDF = make_pdf_bytes(
    [
        ["GroundTruth stores uploaded documents as evidence."],
        ["This second page talks about retrieval and citations."],
    ]
)


@pytest.fixture()
def client(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/gt4.db")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    app.dependency_overrides[get_session_factory] = lambda: factory
    app.dependency_overrides[get_embedding_provider] = lambda: FakeEmbeddingProvider()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


STATIC_DIR = Path(groundtruth.api.__file__).parent / "static"

# --------------------------------------------------------------------------
# The page and its assets
# --------------------------------------------------------------------------


def test_index_serves_the_one_page_ui():
    with TestClient(app) as bare_client:
        response = bare_client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    html = response.text
    # GT-57 replaced the single-answer regions (answer-area, abstain-area,
    # evidence-list) with per-turn regions inside the conversation thread;
    # the list below tracks the redesigned structure instead.
    for element_id in (
        "status-dot",
        "library-count",
        "upload-form",
        "file-input",
        "dropzone",
        "upload-activity",
        "upload-progress",
        "upload-result",
        "documents-list",
        "documents-empty",
        "ask-form",
        "question-input",
        "conversation-thread",
        "conversation-empty",
        "clear-conversation",
        "error-banner",
    ):
        assert f'id="{element_id}"' in html, element_id
    assert "/static/style.css" in html
    assert "/static/app.js" in html


def test_static_assets_are_served():
    with TestClient(app) as bare_client:
        js = bare_client.get("/static/app.js")
        css = bare_client.get("/static/style.css")
    assert js.status_code == 200
    assert "textContent" in js.text
    assert css.status_code == 200
    assert ".evidence-card" in css.text


def test_ui_javascript_never_renders_html_strings():
    """XSS guard: app.js must not contain the HTML-string DOM API at
    all; every document-derived string goes through textContent."""
    source = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    assert "inner" + "HTML" not in source
    assert "outer" + "HTML" not in source
    assert "document.write" not in source
    assert "textContent" in source


# --------------------------------------------------------------------------
# GET /api/v1/documents
# --------------------------------------------------------------------------


def test_documents_list_is_empty_before_any_upload(client):
    response = client.get("/api/v1/documents")
    assert response.status_code == 200
    assert response.json() == []


def test_documents_list_contains_uploaded_document(client):
    upload = client.post(
        "/api/v1/documents",
        files={"file": ("notes.pdf", TWO_PAGE_PDF, "application/pdf")},
    )
    assert upload.status_code == 200

    response = client.get("/api/v1/documents")
    assert response.status_code == 200
    documents = response.json()
    assert len(documents) == 1
    (doc,) = documents
    assert doc["document_id"] == upload.json()["document_id"]
    assert doc["title"] == "notes"
    assert doc["filename"] == "notes.pdf"
    assert doc["pages"] == 2
    assert doc["chunk_count"] == upload.json()["chunks"] == 2
    assert doc["created_at"] is not None


def test_documents_list_without_database_url_is_503(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with TestClient(app) as bare_client:
        response = bare_client.get("/api/v1/documents")
    assert response.status_code == 503
    assert "DATABASE_URL" in response.json()["detail"]
