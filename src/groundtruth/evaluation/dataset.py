from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


@dataclass(frozen=True)
class RetrievalCase:
    """A versioned retrieval evaluation case with explicit gold evidence IDs."""

    case_id: str
    question: str
    gold_chunk_ids: frozenset[str]
    answerable: bool = True

    def __post_init__(self) -> None:
        if not self.case_id.strip():
            raise ValueError("case_id must not be empty")
        if not self.question.strip():
            raise ValueError("question must not be empty")
        if self.answerable and not self.gold_chunk_ids:
            raise ValueError("answerable cases require at least one gold chunk")
        if not self.answerable and self.gold_chunk_ids:
            raise ValueError("unanswerable cases cannot declare gold evidence")


def case_from_mapping(item: Mapping[str, object]) -> RetrievalCase:
    """Parse a JSON-compatible evaluation case without silently inventing labels."""

    gold = item.get("gold_chunk_ids", [])
    if not isinstance(gold, list) or not all(isinstance(value, str) for value in gold):
        raise ValueError("gold_chunk_ids must be a list of strings")
    answerable = item.get("answerable", True)
    if not isinstance(answerable, bool):
        raise ValueError("answerable must be boolean")
    return RetrievalCase(
        case_id=str(item.get("case_id", "")),
        question=str(item.get("question", "")),
        gold_chunk_ids=frozenset(gold),
        answerable=answerable,
    )


def load_cases(items: Iterable[Mapping[str, object]]) -> tuple[RetrievalCase, ...]:
    return tuple(case_from_mapping(item) for item in items)
