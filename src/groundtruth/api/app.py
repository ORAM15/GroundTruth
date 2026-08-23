from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException, UploadFile
from pydantic import BaseModel, Field

app = FastAPI(title="GroundTruth", version="0.1.0")


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=20_000)
    top_k: int = Field(default=10, ge=1, le=100)


class QueryResponse(BaseModel):
    decision: str
    message: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, str]:
    if not os.getenv("DATABASE_URL"):
        raise HTTPException(status_code=503, detail="Evidence store is not configured.")
    return {"status": "ready"}


@app.post("/api/v1/documents")
async def ingest_document(file: UploadFile):
    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(status_code=415, detail="Only PDF uploads are supported in the MVP.")
    # Full persistence is deliberately separated from parsing so the loader remains testable.
    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Uploaded document is empty.")
    return {"status": "accepted", "filename": file.filename, "bytes": len(payload)}


@app.post("/api/v1/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    # Trust behavior: until an evidence store is configured, never fabricate an answer.
    return QueryResponse(
        decision="ABSTAIN",
        message="No authorized evidence store is configured; GroundTruth will not fabricate an answer.",
    )
