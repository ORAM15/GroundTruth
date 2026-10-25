"""GT-44: the documents list must reflect a stored document without a
manual reload, and must never claim "no documents" when it simply
failed to load.

Investigation note: the literal 2026-10-23 observation (list stale
even after a reload) could NOT be reproduced from the current code —
both the synchronous upload path and the async polling success path
already call ``refreshDocuments()``. What the code did have, and what
produces exactly that symptom on a sleepy free-tier instance, was:

* a one-shot documents fetch: a single transient failure left the
  panel on its initial "No documents stored yet" state, and
* polling that stopped forever on the first transient ingestion-status
  error, orphaning both the job indicator and the success refresh.

This test file locks in the refresh contract and the two robustness
fixes. Like the other UI tests it is structural: app.js runs in a
browser, so the shipped file is scanned for the behaviour markers.
"""

from __future__ import annotations

import re
from pathlib import Path

import groundtruth.api

STATIC_DIR = Path(groundtruth.api.__file__).parent / "static"


def _js() -> str:
    return (STATIC_DIR / "app.js").read_text(encoding="utf-8")


def test_upload_success_paths_refresh_the_documents_list():
    """Both terminal upload outcomes re-fetch the list: the synchronous
    "Stored ..." path and the async polling success path."""
    js = _js()
    # Initial page load + sync upload + async success = at least three
    # refresh call sites; the two upload paths await theirs.
    assert js.count("refreshDocuments()") >= 3
    assert js.count("await refreshDocuments();") >= 2


def test_documents_fetch_retries_transient_failures():
    """A single dropped list fetch must not leave the panel stale."""
    js = _js()
    assert "DOCUMENTS_FETCH_ATTEMPTS" in js
    attempts = re.search(r"DOCUMENTS_FETCH_ATTEMPTS\s*=\s*(\d+)", js)
    assert attempts is not None and int(attempts.group(1)) >= 2
    assert "DOCUMENTS_FETCH_RETRY_MS" in js
    # The retry loop sleeps between attempts instead of failing at once.
    assert re.search(r"attempt\s*<\s*DOCUMENTS_FETCH_ATTEMPTS", js) is not None
    assert "await sleep(DOCUMENTS_FETCH_RETRY_MS)" in js


def test_failed_documents_load_does_not_claim_an_empty_store():
    """On a failed load the empty-state paragraph is hidden: a failed
    load is not an empty store, and the panel must not say otherwise."""
    js = _js()
    assert "empty.hidden = true;" in js


def test_polling_survives_transient_status_errors():
    """Polling stops only after several consecutive status-check
    failures, not on the first transient error."""
    js = _js()
    assert "INGESTION_STATUS_MAX_FAILURES" in js
    failures = re.search(r"INGESTION_STATUS_MAX_FAILURES\s*=\s*(\d+)", js)
    assert failures is not None and int(failures.group(1)) >= 2
    assert "consecutiveFailures" in js
    assert "consecutiveFailures = 0;" in js  # reset on a good response
    assert "consecutiveFailures >= INGESTION_STATUS_MAX_FAILURES" in js
