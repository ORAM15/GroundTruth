"""Grounded answer generation (GT-3): provider, prompt builder, and
citation verification."""

from groundtruth.generation.citations import (
    CitationVerification,
    extract_citations,
    verify_citations,
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
    "EvidencePassage",
    "GeminiGenerationProvider",
    "GenerationError",
    "GenerationProvider",
    "build_grounded_prompt",
    "extract_citations",
    "verify_citations",
]
