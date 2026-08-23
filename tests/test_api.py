from fastapi.testclient import TestClient

from groundtruth.api.app import app


client = TestClient(app)


def test_health_is_live():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_refuses_without_evidence_store(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    response = client.get("/ready")
    assert response.status_code == 503


def test_query_abstains_without_evidence_store():
    response = client.post("/api/v1/query", json={"question": "What is GroundTruth?"})
    assert response.status_code == 200
    assert response.json()["decision"] == "ABSTAIN"


def test_document_upload_rejects_non_pdf():
    response = client.post(
        "/api/v1/documents",
        files={"file": ("note.txt", b"not a pdf", "text/plain")},
    )
    assert response.status_code == 415
