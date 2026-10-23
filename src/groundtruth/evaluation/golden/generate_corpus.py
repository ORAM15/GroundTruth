"""Corpus generation for the GT-5 golden dataset.

The corpus sources are the plain-text files in ``corpus/`` next to this
module — one fact per line, and (via the production chunker) one chunk per
line. The PDFs uploaded during evaluation are generated from those sources
by :func:`build_pdf`, the same minimal hand-rolled PDF writer the test
suites use (Helvetica, one ``Tj`` per line, no PDF-writing dependency), so
the corpus is fully reproducible from committed sources: no opaque binary
blobs are committed.

Run as a script to materialise the PDFs under ``corpus_pdf/`` for
inspection::

    python -m groundtruth.evaluation.golden.generate_corpus
"""

from __future__ import annotations

from pathlib import Path

GOLDEN_DIR = Path(__file__).parent
CORPUS_DIR = GOLDEN_DIR / "corpus"
GENERATED_PDF_DIR = GOLDEN_DIR / "corpus_pdf"


def build_pdf(lines: list[str]) -> bytes:
    """Build a minimal one-page PDF (Helvetica, one Tj per line) that
    pypdf can extract text from. Identical approach to the synthetic-PDF
    helper in the GT-1/GT-2/GT-3 test suites."""

    def escape(text: str) -> str:
        return text.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")

    objects: list[bytes] = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    objects.append(
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>"
    )
    stream_lines = ["BT", "/F1 12 Tf", "14 TL", "72 720 Td"]
    for index, line in enumerate(lines):
        if index:
            stream_lines.append("T*")
        stream_lines.append(f"({escape(line)}) Tj")
    stream_lines.append("ET")
    stream = "\n".join(stream_lines).encode()
    objects.append(
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream"
    )
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    out = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    xref_start = len(out)
    size = len(objects) + 1
    out += f"xref\n0 {size}\n".encode()
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {size} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF\n".encode()
    return bytes(out)


def corpus_documents() -> list[tuple[str, str]]:
    """The corpus as ``(pdf_filename, text)`` pairs, sorted by filename
    so seeding order is deterministic. Each ``.txt`` source becomes one
    PDF named after it."""
    documents = []
    for path in sorted(CORPUS_DIR.glob("*.txt")):
        documents.append((f"{path.stem}.pdf", path.read_text(encoding="utf-8")))
    return documents


def corpus_pdfs() -> list[tuple[str, bytes]]:
    """The corpus rendered to PDF bytes: ``(pdf_filename, payload)``."""
    return [
        (filename, build_pdf([line for line in text.splitlines() if line.strip()]))
        for filename, text in corpus_documents()
    ]


def main() -> None:
    GENERATED_PDF_DIR.mkdir(exist_ok=True)
    for filename, payload in corpus_pdfs():
        target = GENERATED_PDF_DIR / filename
        target.write_bytes(payload)
        print(f"wrote {target} ({len(payload)} bytes)")


if __name__ == "__main__":
    main()
