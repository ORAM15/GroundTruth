"""GT-57: production UI/UX redesign — document library, conversation Q&A,
evidence display. Frontend only; the API is unchanged.

Structural tests (same pattern as the other UI tests): the shipped page
and script are scanned for the redesign's markers, and the page is
served to confirm the new panels exist. No live browser is involved,
so these tests lock in structure and behaviour markers, not pixels —
the owner judges the look from the PR description after merging.
"""

from __future__ import annotations

from pathlib import Path

import groundtruth.api
from groundtruth.api.app import app

STATIC_DIR = Path(groundtruth.api.__file__).parent / "static"


def _html() -> str:
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        response = client.get("/")
    assert response.status_code == 200
    return response.text


def _js() -> str:
    return (STATIC_DIR / "app.js").read_text(encoding="utf-8")


def _css() -> str:
    return (STATIC_DIR / "style.css").read_text(encoding="utf-8")


def test_redesigned_panels_exist_in_the_page():
    """Library, upload activity, and conversation panels, plus the
    product header (brand mark, library count, service status)."""
    html = _html()
    for element_id in (
        "library-count",
        "dropzone",
        "upload-activity",
        "upload-progress",
        "documents-list",
        "conversation-thread",
        "conversation-empty",
        "clear-conversation",
    ):
        assert f'id="{element_id}"' in html, element_id
    assert "brand-mark" in html
    assert "Evidence library" in html
    assert "Ask your documents" in html


def test_library_rows_carry_filename_pages_chunks_date_and_status():
    """Each library row renders filename, page/chunk counts, stored
    date, and a Stored status pill — and the header count tracks the
    number of stored documents."""
    js = _js()
    assert '"doc-card"' in js
    assert '"doc-name"' in js
    assert '"doc-meta"' in js
    assert '"doc-status"' in js
    assert '"Stored"' in js
    assert 'stored " + new Date(doc.created_at).toLocaleString()' in js
    assert 'count.textContent = String(documents.length)' in js
    # The badge is a plain "PDF" label, not an image or emoji asset.
    assert '"doc-badge"' in js


def test_conversation_thread_keeps_question_history():
    """Questions append as turns (question bubble + answer/decline +
    per-turn evidence), instead of overwriting one answer region."""
    js = _js()
    assert "conversation-thread" in js
    assert "turn-question" in js
    assert "turn-answer" in js
    assert "turn-decline" in js
    assert "turn-evidence" in js
    assert "appendTurn" in js
    assert "clear-conversation" in js
    # Chips still scroll to their own turn's evidence card.
    assert "scrollIntoView" in js
    assert "evidence-card-" in js


def test_upload_activity_never_goes_silent():
    """The activity card covers every upload state: uploading,
    processing with chunk progress, stored, interrupted-retry, and
    failure — and the progress bar is driven from chunk counts."""
    js = _js()
    assert "setUploadActivity" in js
    assert '"Uploading' in js
    assert '"Processing: "' in js
    assert '"Stored: "' in js
    assert "Ingestion was interrupted" in js
    assert "upload the document again to retry" in js
    assert "upload-progress" in js
    assert "chunks_done" in js and "chunks_total" in js
    # Drag-and-drop feeds the same file input as the chooser.
    assert "dataTransfer" in js
    assert "drag-over" in js


def test_decline_stays_plain_language_with_no_internal_ids():
    """Declines show the server message plus a plain-language hint
    about why it happened and what helps — never an id."""
    js = _js()
    assert "GroundTruth declined to answer" in js
    assert "decline-hint" in js
    assert "A more specific " in js
    # No chunk-id formatting anywhere in user-facing decline text.
    assert "chunk:" not in js


def test_product_styling_and_mobile_layout():
    """A real visual identity (dark header, accent, cards) and a
    stacked single-column layout on narrow screens."""
    css = _css()
    assert ".brand-mark" in css
    assert ".conversation-thread" in css
    assert ".turn-question" in css
    assert ".doc-card" in css
    assert "@media (max-width: 820px)" in css
    assert "grid-template-areas" in css


def test_redesign_keeps_the_xss_guard():
    """The rewrite still renders document-derived strings only via
    textContent — no HTML-string DOM API anywhere in the script."""
    js = _js()
    assert "inner" + "HTML" not in js
    assert "outer" + "HTML" not in js
    assert "document.write" not in js
    assert "textContent" in js


def test_redesign_keeps_existing_api_flows():
    """Upload (200/202), ingestion polling, and query endpoints are
    unchanged in the script — presentation only."""
    js = _js()
    assert '"/api/v1/documents"' in js
    assert '"/api/v1/query"' in js
    assert "/ingestion" in js
    assert "setInterval" in js
    assert "202" in js
    assert "refreshDocuments()" in js
