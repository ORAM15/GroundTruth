"""Grounded answer generation (GT-3): provider, prompt builder, and
citation verification."""

from groundtruth.generation.citations import (
    CitationVerification,
    EvidenceChunk,
    SelfContainedCitation,
    extract_citations,
    extract_self_contained_citations,
    verify_citations,
    verify_self_contained_citations,
)
from groundtruth.generation.prompt import (
    EvidencePassage,
    build_grounded_prompt,
)
from groundtruth.generation.provider import (
    GeminiGenerationProvider,
    GenerationError,
    GenerationProvider,
)

__all__ = [
    "CitationVerification",
    "EvidenceChunk",
    "EvidencePassage",
    "GeminiGenerationProvider",
    "GenerationError",
    "GenerationProvider",
    "SelfContainedCitation",
    "build_grounded_prompt",
    "extract_citations",
    "extract_self_contained_citations",
    "verify_citations",
    "verify_self_contained_citations",
]
