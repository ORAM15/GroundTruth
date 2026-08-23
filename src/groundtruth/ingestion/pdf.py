from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Iterable

from groundtruth.domain.models import Chunk, DocumentVersion, Section


@dataclass(frozen=True)
class ParsedBlock:
    text: str
    page: int | None = None
    kind: str = "text"
    heading_level: int | None = None


@dataclass(frozen=True)
class ParsedDocument:
    title: str
    source_uri: str
    blocks: tuple[ParsedBlock, ...]
    content_hash: str


class PdfLoader:
    """PDF adapter. Parser output is normalized into GroundTruth IR."""

    def load(self, path: str | Path) -> ParsedDocument:
        from pypdf import PdfReader

        source = Path(path)
        reader = PdfReader(str(source))
        blocks: list[ParsedBlock] = []
        page_texts: list[str] = []
        for page_number, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            page_texts.append(text)
            if text:
                blocks.append(ParsedBlock(text=text, page=page_number))
        payload = "\n".join(page_texts)
        return ParsedDocument(
            title=source.stem,
            source_uri=str(source),
            blocks=tuple(blocks),
            content_hash=sha256(payload.encode("utf-8")).hexdigest(),
        )


class StructureAwareChunker:
    """Conservative first-pass chunker preserving page and section lineage."""

    def __init__(self, max_chars: int = 1800, overlap_chars: int = 180) -> None:
        if max_chars <= overlap_chars or overlap_chars < 0:
            raise ValueError("max_chars must be greater than overlap_chars >= 0")
        self.max_chars = max_chars
        self.overlap_chars = overlap_chars

    def chunk(self, parsed: ParsedDocument, version_id: str) -> DocumentVersion:
        sections: list[Section] = []
        chunks: list[Chunk] = []
        current_section: Section | None = None
        section_counter = 0
        chunk_counter = 0

        for block in parsed.blocks:
            lines = [line.strip() for line in block.text.splitlines() if line.strip()]
            for line in lines:
                if self._looks_like_heading(line):
                    section_counter += 1
                    current_section = Section(
                        section_id=f"{version_id}:section:{section_counter}",
                        title=line,
                        level=1,
                        ordinal=section_counter,
                        structural_path=(line,),
                    )
                    sections.append(current_section)
                    continue
                for text in self._split(line):
                    chunk_counter += 1
                    chunks.append(
                        Chunk(
                            chunk_id=f"{version_id}:chunk:{chunk_counter}",
                            document_version_id=version_id,
                            text=text,
                            section_id=current_section.section_id if current_section else None,
                            ordinal=chunk_counter,
                            page_start=block.page,
                            page_end=block.page,
                            source_span={"type": "page_text", "page": block.page},
                            structural_path=current_section.structural_path if current_section else (),
                        )
                    )

        return DocumentVersion(
            version_id=version_id,
            document_id=version_id.split(":", 1)[0],
            version_label="initial",
            source_uri=parsed.source_uri,
            content_hash=parsed.content_hash,
            sections=tuple(sections),
            chunks=tuple(chunks),
        )

    def _split(self, text: str) -> Iterable[str]:
        if len(text) <= self.max_chars:
            yield text
            return
        start = 0
        while start < len(text):
            end = min(start + self.max_chars, len(text))
            piece = text[start:end].strip()
            if piece:
                yield piece
            if end == len(text):
                break
            start = end - self.overlap_chars

    @staticmethod
    def _looks_like_heading(line: str) -> bool:
        stripped = line.strip()
        if len(stripped) > 140 or len(stripped.split()) > 16:
            return False
        upper = stripped.upper()
        return (
            upper.startswith(("UNIT ", "CHAPTER ", "SECTION "))
            or stripped.endswith(":")
            or (stripped.isupper() and len(stripped.split()) <= 12)
        )
