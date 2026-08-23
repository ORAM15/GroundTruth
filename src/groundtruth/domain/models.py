from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from hashlib import sha256
from typing import Any


def content_hash(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Section:
    section_id: str
    title: str
    level: int
    ordinal: int
    parent_section_id: str | None = None
    structural_path: tuple[str, ...] = ()


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    document_version_id: str
    text: str
    section_id: str | None
    ordinal: int
    page_start: int | None = None
    page_end: int | None = None
    source_span: dict[str, Any] = field(default_factory=dict)
    structural_path: tuple[str, ...] = ()
    content_hash: str = ""
    representation_version: str = "REP-01"

    def __post_init__(self) -> None:
        if not self.content_hash:
            object.__setattr__(self, "content_hash", content_hash(self.text))


@dataclass(frozen=True)
class DocumentVersion:
    version_id: str
    document_id: str
    version_label: str
    source_uri: str
    content_hash: str
    effective_from: date | None = None
    effective_until: date | None = None
    sections: tuple[Section, ...] = ()
    chunks: tuple[Chunk, ...] = ()


@dataclass(frozen=True)
class Document:
    document_id: str
    title: str
    source_type: str
    source_uri: str
    created_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)
    versions: tuple[DocumentVersion, ...] = ()
