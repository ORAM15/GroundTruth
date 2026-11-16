"""Citation verification for generated answers (GT-3, rebuild slice 2
— issue #68).

A generated answer is only returned to the caller if its citations check
out against the evidence that was actually retrieved:

* at least one ``[chunk_id]`` marker must be present, and
* every marker must name a chunk in the retrieved evidence set.

Slice 2 adds the self-contained form on top of that gate: a rendered
citation must read ``Title, p.N: "short verbatim quote" [chunk_id]``,
and the title, page and quoted words must match the retrieved chunk
they name. A bare ``[chunk_id]`` marker, a wrong title or page, or a
quote that does not appear verbatim in the cited chunk all fail
verification, and the endpoint abstains instead of returning the
unverifiable text. This is what keeps "answer with citations" from
degenerating into "answer with citation-shaped decoration": citation
correctness is enforced in code, not trusted to the model.
"""

from __future__ import annotations

import re
from collections.abc import Collection, Mapping
from dataclasses import dataclass

_MARKER = re.compile(r"\[([^\[\]\n]+)\]")

# A self-contained citation: Title, p.N: "verbatim quote" [chunk_id].
# The title is non-greedy up to the ", p.N:" that introduces the quote;
# titles in this corpus do not themselves contain ", p.<digits>:".
_SELF_CONTAINED = re.compile(
    r'(.+?),\s*p\.\s*(\d+)\s*:\s*"([^"]+)"\s*\[([^\[\]\n]+)\]'
)

_WHITESPACE = re.compile(r"\s+")


def _normalise(text: str) -> str:
    """Collapse whitespace so a quote that reflows across lines still
    matches the chunk text it was copied from."""
    return _WHITESPACE.sub(" ", text).strip()


def _quote_matches(quote: str, chunk_text: str) -> bool:
    """True when ``quote`` appears verbatim in ``chunk_text`` after
    whitespace normalisation. A quote must be at least three characters:
    a one- or two-character "quote" proves nothing."""
    normalised = _normalise(quote).strip("…")
    return len(normalised) >= 3 and normalised in _normalise(chunk_text)


@dataclass(frozen=True)
class SelfContainedCitation:
    """One rendered self-contained citation parsed out of an answer."""

    title: str
    page: int
    quote: str
    chunk_id: str


@dataclass(frozen=True)
class EvidenceChunk:
    """One retrieved chunk, as verification needs to see it: the metadata
    a rendered citation claims (title, pages) and the full text the quote
    must appear in verbatim."""

    chunk_id: str
    title: str | None
    page_start: int | None
    page_end: int | None
    text: str


def _title_matches(cited_title: str, expected_title: str) -> bool:
    """True when ``expected_title`` is the tail of ``cited_title``: a
    citation sits inside a sentence ("GroundTruth stores documents as
    evidence notes, p.1: ..."), so the title is the end of the text
    before ``, p.N:``, not the whole of it. The character before the
    tail must not be alphanumeric, so "field notes" does not pass for
    a chunk titled "notes" when the tail starts mid-word."""
    actual = _normalise(cited_title)
    expected = _normalise(expected_title)
    index = actual.rfind(expected)
    return (
        index >= 0
        and index + len(expected) == len(actual)
        and (index == 0 or not actual[index - 1].isalnum())
    )


def extract_self_contained_citations(answer: str) -> list[SelfContainedCitation]:
    """All self-contained citations in ``answer``, de-duplicated, in the
    order they first appear. ``title`` is the text immediately before
    ``, p.N:`` — the cited document's title is its tail (see
    ``_title_matches``); a citation mid-sentence carries prose before
    the title, and the parser cannot know where the title starts."""
    seen: list[SelfContainedCitation] = []
    for match in _SELF_CONTAINED.finditer(answer):
        citation = SelfContainedCitation(
            title=match.group(1).strip(),
            page=int(match.group(2)),
            quote=match.group(3),
            chunk_id=match.group(4).strip(),
        )
        if citation not in seen:
            seen.append(citation)
    return seen


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


def verify_self_contained_citations(
    answer: str, evidence: Mapping[str, EvidenceChunk]
) -> CitationVerification:
    """Check ``answer``'s self-contained citations against the retrieved
    evidence (issue #68). The chunk-id gate runs first — no markers, or
    a marker naming a chunk that was never retrieved, fails exactly as
    ``verify_citations`` reports it. Then every rendered citation must
    be self-contained and must match the chunk it names: the title
    (when the chunk has one), the page (the chunk's first page, or any
    page in its page range), and a quote that appears verbatim in the
    chunk's text. A bare ``[chunk_id]`` marker with no self-contained
    citation is a failure, not a pass: the answer text itself must carry
    the receipts."""
    base = verify_citations(answer, evidence.keys())
    if not base.ok:
        return base
    rendered = extract_self_contained_citations(answer)
    if not rendered:
        return CitationVerification(
            ok=False,
            cited_ids=base.cited_ids,
            invalid_ids=(),
            reason=(
                "the generated answer contained no self-contained "
                'citations (Title, p.N: "quote" [chunk_id])'
            ),
        )
    covered = {citation.chunk_id for citation in rendered}
    bare = tuple(marker for marker in base.cited_ids if marker not in covered)
    if bare:
        return CitationVerification(
            ok=False,
            cited_ids=base.cited_ids,
            invalid_ids=bare,
            reason=(
                "citation(s) were not self-contained: "
                f"{', '.join(bare)}"
            ),
        )
    for citation in rendered:
        chunk = evidence[citation.chunk_id]
        if chunk.title is not None and not _title_matches(citation.title, chunk.title):
            return CitationVerification(
                ok=False,
                cited_ids=base.cited_ids,
                invalid_ids=(citation.chunk_id,),
                reason=(
                    f"citation to {citation.chunk_id} named the wrong "
                    f"document title: {citation.title!r} "
                    f"(expected {chunk.title!r})"
                ),
            )
        if chunk.page_start is not None:
            last_page = chunk.page_end if chunk.page_end is not None else chunk.page_start
            if not chunk.page_start <= citation.page <= last_page:
                return CitationVerification(
                    ok=False,
                    cited_ids=base.cited_ids,
                    invalid_ids=(citation.chunk_id,),
                    reason=(
                        f"citation to {citation.chunk_id} named the wrong "
                        f"page: p.{citation.page} "
                        f"(chunk spans p.{chunk.page_start}"
                        + (
                            f"–{chunk.page_end}"
                            if chunk.page_end is not None
                            and chunk.page_end != chunk.page_start
                            else ""
                        )
                        + ")"
                    ),
                )
        if not _quote_matches(citation.quote, chunk.text):
            return CitationVerification(
                ok=False,
                cited_ids=base.cited_ids,
                invalid_ids=(citation.chunk_id,),
                reason=(
                    f"citation to {citation.chunk_id} quoted words that "
                    "do not appear verbatim in the cited chunk: "
                    f"{citation.quote!r}"
                ),
            )
    return CitationVerification(
        ok=True,
        cited_ids=tuple(dict.fromkeys(citation.chunk_id for citation in rendered)),
        invalid_ids=(),
        reason=(
            "every self-contained citation resolves to a retrieved chunk "
            "with a matching title, page and verbatim quote"
        ),
    )
