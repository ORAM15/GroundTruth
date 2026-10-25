"""Topic-less question guidance (GT-61 objective 4).

Some questions have no discernible topic — "what do the documents say
about?", "tell me everything" — and no retrieval over them can produce
a grounded answer: there is nothing to ground an overview *of*. The
old behaviour declined those questions with a bare abstention, which
reads to users as "the product does not answer".

The new behaviour is guidance, not an answer: name what is stored and
teach the question shape that works ("what does <document> say about
<topic>?"). Guidance NEVER fabricates summary content and NEVER claims
citations it does not have — example questions are templates derived
from stored document titles only.

Detection is deliberately conservative: only prompts that match the
exact generic set below (after case/whitespace/punctuation
normalisation) route to guidance. Anything with a discernible topic —
including "tell me everything about deployment" — takes the normal
retrieval + generation + verification path. When in doubt, the normal
path wins: a missed guidance is a plain decline, but a misrouted
topical question would be a refused answer.
"""

from __future__ import annotations

import re

# Normalised (lowercased, whitespace-collapsed, trailing punctuation
# stripped, leading "please" removed) prompts with no discernible topic.
_TOPICLESS = frozenset(
    [
        "what do the documents say about",
        "what do the documents say",
        "what do these documents say about",
        "what do these documents say",
        "what do my documents say about",
        "what do my documents say",
        "what do the documents say about it",
        "what do the documents say about this",
        "what do the documents say about them",
        "what do the documents say about everything",
        "what does the document say about",
        "what does the document say",
        "what does this document say about",
        "what does this document say",
        "what do the document say about",
        "what do the document say",
        "tell me everything",
        "tell me everything about the documents",
        "tell me everything about these documents",
        "tell me everything about my documents",
        "give me everything",
        "give me a summary of everything",
        "summarize everything",
        "summarise everything",
        "summarize all documents",
        "summarise all documents",
        "summarize the documents",
        "summarise the documents",
        "summarize all of it",
        "summarise all of it",
        "what is in the documents",
        "what is in these documents",
        "what is in my documents",
        "what are the documents about",
        "what are these documents about",
    ]
)

_WHITESPACE = re.compile(r"\s+")
_TRAILING_PUNCT = re.compile(r"[?.!]+\s*$")
_LEADING_PLEASE = re.compile(r"^please\s+")


def normalize_question(question: str) -> str:
    """Lowercase, collapse whitespace, drop a leading 'please' and any
    trailing question/exclamation marks — so 'What do the documents
    say about?' and 'what do the documents say about' match alike."""
    text = _WHITESPACE.sub(" ", question.strip().lower())
    text = _LEADING_PLEASE.sub("", text)
    return _TRAILING_PUNCT.sub("", text).strip()


def is_topicless_question(question: str) -> bool:
    """True only for clearly generic prompts with no discernible topic."""
    return normalize_question(question) in _TOPICLESS


def guidance_message(document_count: int) -> str:
    """Plain-language guidance: what is stored, and the question shape
    that works. Contains no summary content and no citations."""
    noun = "document" if document_count == 1 else "documents"
    return (
        f"I can't summarize everything at once — the library holds "
        f"{document_count} stored {noun}. Pick one and a topic, then ask "
        f"what it says about that topic; the answer will cite the exact "
        f"document and page it came from."
    )


def guidance_examples(titles: list[str], limit: int = 3) -> list[str]:
    """Example questions as templates derived from stored titles only.
    The ellipsis marks the slot the user must fill with a topic — the
    examples assert nothing about any document's content."""
    return [f'What does "{title}" say about ...?' for title in titles[:limit]]
