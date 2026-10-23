"""Citation verification for generated answers (GT-3).

A generated answer is only returned to the caller if its citations check
out against the evidence that was actually retrieved:

* at least one ``[chunk_id]`` marker must be present, and
* every marker must name a chunk in the retrieved evidence set.

Anything else — no citations, or a citation to a chunk the model invented —
fails verification, and the endpoint abstains instead of returning the
unverifiable text. This is what keeps "answer with citations" from
degenerating into "answer with citation-shaped decoration": citation
correctness is enforced in code, not trusted to the model.
"""

from __future__ import annotations

import re
from collections.abc import Collection
from dataclasses import dataclass

_MARKER = re.compile(r"\[([^\[\]\n]+)\]")


def extract_citations(answer: str) -> list[str]:
    """All ``[...]`` citation markers in ``answer``, de-duplicated, in the
    order they first appear."""
    seen: list[str] = []
    for match in _MARKER.finditer(answer):
        marker = match.group(1).strip()
        if marker and marker not in seen:
            seen.append(marker)
    return seen


@dataclass(frozen=True)
class CitationVerification:
    ok: bool
    cited_ids: tuple[str, ...]
    invalid_ids: tuple[str, ...]
    reason: str


def verify_citations(answer: str, allowed_ids: Collection[str]) -> CitationVerification:
    """Check ``answer``'s citation markers against the retrieved chunk ids."""
    cited = extract_citations(answer)
    if not cited:
        return CitationVerification(
            ok=False,
            cited_ids=(),
            invalid_ids=(),
            reason="the generated answer contained no citations",
        )
    allowed = set(allowed_ids)
    invalid = tuple(marker for marker in cited if marker not in allowed)
    if invalid:
        return CitationVerification(
            ok=False,
            cited_ids=tuple(cited),
            invalid_ids=invalid,
            reason=(
                "the generated answer cited chunk(s) that were not in the "
                f"retrieved evidence: {', '.join(invalid)}"
            ),
        )
    return CitationVerification(
        ok=True,
        cited_ids=tuple(cited),
        invalid_ids=(),
        reason="every citation resolves to a retrieved evidence chunk",
    )
