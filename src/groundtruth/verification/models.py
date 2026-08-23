from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Sequence

from groundtruth.domain.models import Chunk


class VerificationVerdict(StrEnum):
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class FinalDecision(StrEnum):
    ANSWER = "ANSWER"
    ANSWER_WITH_QUALIFICATION = "ANSWER_WITH_QUALIFICATION"
    ABSTAIN = "ABSTAIN"
    CONFLICT = "CONFLICT"
    FAILED = "FAILED"


@dataclass(frozen=True)
class Claim:
    claim_id: str
    text: str


@dataclass(frozen=True)
class ClaimEvidence:
    claim_id: str
    chunk_id: str
    rationale: str


@dataclass(frozen=True)
class VerificationResult:
    claim: Claim
    verdict: VerificationVerdict
    evidence: tuple[ClaimEvidence, ...] = ()


@dataclass(frozen=True)
class EvidenceAssessment:
    decision: FinalDecision
    reason: str


def assess_evidence(chunks: Sequence[Chunk]) -> EvidenceAssessment:
    if not chunks:
        return EvidenceAssessment(FinalDecision.ABSTAIN, "No evidence was retrieved.")
    return EvidenceAssessment(
        FinalDecision.ABSTAIN,
        "Retrieved material exists, but evidence sufficiency has not been established.",
    )
