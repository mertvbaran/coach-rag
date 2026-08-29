"""Chunking strategies. Every strategy shares the list[Document] -> list[Chunk] signature."""

import re
from dataclasses import dataclass

from loader import Document

SKIP_HEADINGS = {"related", "sources", "kaynaklar", "ilgili"}
MIN_CHUNK_WORDS = 40
FIXED_WINDOW_WORDS = 300
FIXED_WINDOW_OVERLAP = 60


@dataclass
class Chunk:
    doc_slug: str
    doc_path: str
    doc_title: str
    doc_type: str
    heading: str | None
    text: str  # full text to embed, including the header prefix
    chunk_id: str


def _header_prefix(doc: Document) -> str:
    tags = ", ".join(doc.tags) if doc.tags else ""
    return f"{doc.title} ({doc.doc_type})\ntags: {tags}\n\n"


def readable_text(chunk: dict, limit: int | None = None) -> str:
    """The passage as a reader should see it, rather than as it was embedded.

    A chunk's text is the exact string that went to the embedding model, so it
    opens with the header _header_prefix() adds and then repeats the heading
    the chunk was cut at -- both useful to the retriever, both noise on screen
    next to a file path that already names them. Lives here because this is
    the module that puts them there.

    The rest of the markdown is left alone: these are notes, and `code` and
    **emphasis** are how they read.
    """
    body = chunk["text"]

    prefix_end = body.find("\n\n")
    if prefix_end != -1 and body[:prefix_end].startswith(str(chunk.get("doc_title", ""))):
        body = body[prefix_end + 2 :]

    # A chunk can open with more than one heading line: a whole-document chunk
    # starts with the document's "# Title" and then its first "## " section.
    lines = body.splitlines()
    while lines and (not lines[0].strip() or lines[0].lstrip().startswith("#")):
        lines.pop(0)

    text = " ".join("\n".join(lines).split())
    return text[:limit] if limit else text


def chunk_whole_doc(docs: list[Document]) -> list[Chunk]:
    chunks = []
    for doc in docs:
        text = _header_prefix(doc) + doc.body
        chunks.append(
            Chunk(
                doc_slug=doc.slug,
                doc_path=doc.path,
                doc_title=doc.title,
                doc_type=doc.doc_type,
                heading=None,
                text=text,
                chunk_id=f"{doc.slug}#0",
            )
        )
    return chunks


def _heading_key(heading: str) -> str:
    return heading.strip().lower().lstrip("# ").strip()


def chunk_by_heading(docs: list[Document]) -> list[Chunk]:
    chunks = []
    for doc in docs:
        prefix = _header_prefix(doc)

        # Split the body on `## ` level headings (H1 is already stored separately in frontmatter).
        parts = re.split(r"(?m)^## (.+)$", doc.body)
        # parts[0] is the text before the first heading; the rest alternate [heading, text, heading, text, ...].

        sections: list[tuple[str | None, str]] = []
        if parts[0].strip():
            sections.append((None, parts[0].strip()))
        for i in range(1, len(parts), 2):
            heading = parts[i].strip()
            body = parts[i + 1].strip() if i + 1 < len(parts) else ""
            sections.append((heading, body))

        buffer_heading = None
        buffer_text = ""
        idx = 0

        def flush():
            nonlocal buffer_heading, buffer_text, idx
            if buffer_text.strip():
                chunks.append(
                    Chunk(
                        doc_slug=doc.slug,
                        doc_path=doc.path,
                        doc_title=doc.title,
                        doc_type=doc.doc_type,
                        heading=buffer_heading,
                        text=prefix + (f"## {buffer_heading}\n\n" if buffer_heading else "") + buffer_text.strip(),
                        chunk_id=f"{doc.slug}#{idx}",
                    )
                )
                idx += 1
            buffer_heading = None
            buffer_text = ""

        chunks_before = len(chunks)

        for heading, body in sections:
            if heading and _heading_key(heading) in SKIP_HEADINGS:
                continue
            word_count = len(body.split())
            if word_count == 0:
                continue
            if word_count < MIN_CHUNK_WORDS and buffer_text:
                # Merge short sections into the previous chunk instead of embedding fragments.
                buffer_text += f"\n\n## {heading}\n\n{body}" if heading else f"\n\n{body}"
            else:
                flush()
                buffer_heading, buffer_text = heading, body
        flush()

        # Files with no `##` headings at all (mostly flashcards) fall back to
        # whole-document chunking -- but only if the loop above produced
        # nothing, otherwise the same text would be emitted twice.
        if len(chunks) == chunks_before and doc.body.strip():
            chunks.append(
                Chunk(
                    doc_slug=doc.slug,
                    doc_path=doc.path,
                    doc_title=doc.title,
                    doc_type=doc.doc_type,
                    heading=None,
                    text=prefix + doc.body,
                    chunk_id=f"{doc.slug}#0",
                )
            )

    return chunks


def chunk_fixed_window(docs: list[Document]) -> list[Chunk]:
    chunks = []
    for doc in docs:
        prefix = _header_prefix(doc)
        words = doc.body.split()
        if not words:
            continue

        step = FIXED_WINDOW_WORDS - FIXED_WINDOW_OVERLAP
        idx = 0
        i = 0
        while i < len(words):
            window = words[i : i + FIXED_WINDOW_WORDS]
            text = " ".join(window)
            chunks.append(
                Chunk(
                    doc_slug=doc.slug,
                    doc_path=doc.path,
                    doc_title=doc.title,
                    doc_type=doc.doc_type,
                    heading=None,
                    text=prefix + text,
                    chunk_id=f"{doc.slug}#{idx}",
                )
            )
            idx += 1
            if i + FIXED_WINDOW_WORDS >= len(words):
                break
            i += step

    return chunks


CHUNKERS = {
    "whole_doc": chunk_whole_doc,
    "by_heading": chunk_by_heading,
    "fixed_window": chunk_fixed_window,
}


if __name__ == "__main__":
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import VAULT_DIRS, VAULT_ROOT
    from loader import load_vault

    docs = load_vault(VAULT_ROOT, VAULT_DIRS)

    for name, fn in CHUNKERS.items():
        chunks = fn(docs)
        print(f"{name}: {len(chunks)} chunks")
