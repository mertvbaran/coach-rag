"""Tests for the three chunking strategies.

by_heading carries the most logic -- section splitting, dropping link-only
sections, merging short ones -- and is the strategy the system ships with,
so most of the cases below target it.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from chunkers import (
    CHUNKERS,
    FIXED_WINDOW_OVERLAP,
    FIXED_WINDOW_WORDS,
    MIN_CHUNK_WORDS,
    chunk_by_heading,
    chunk_fixed_window,
    chunk_whole_doc,
    readable_text,
)
from loader import Document


def make_doc(body: str, slug: str = "test-doc") -> Document:
    return Document(
        path=f"concepts/{slug}.md",
        slug=slug,
        title="Test Doc",
        tags=["test"],
        doc_type="concept",
        body=body,
    )


def long_section(words: int = MIN_CHUNK_WORDS + 10) -> str:
    return " ".join(["word"] * words)


# --- whole_doc ---

def test_whole_doc_produces_one_chunk_per_document():
    docs = [make_doc("Some content", "a"), make_doc("Other content", "b")]
    chunks = chunk_whole_doc(docs)
    assert len(chunks) == 2
    assert {c.doc_slug for c in chunks} == {"a", "b"}


def test_every_chunk_carries_the_title_and_tags_prefix():
    """All three strategies prepend the same header so the comparison between
    them is not confounded by differing context."""
    doc = make_doc("## Section\n\n" + long_section())
    for name, fn in CHUNKERS.items():
        for chunk in fn([doc]):
            assert "Test Doc" in chunk.text, f"{name} dropped the title"
            assert "test" in chunk.text, f"{name} dropped the tags"


# --- by_heading ---

def test_by_heading_splits_on_level_two_headings():
    body = f"## First\n\n{long_section()}\n\n## Second\n\n{long_section()}"
    chunks = chunk_by_heading([make_doc(body)])
    assert len(chunks) == 2
    assert [c.heading for c in chunks] == ["First", "Second"]


def test_by_heading_drops_link_only_sections():
    """`## Related` and `## Sources` hold nothing but wikilinks -- embedding
    them adds noise without adding retrievable content."""
    body = (
        f"## Real Content\n\n{long_section()}\n\n"
        "## Related\n\n- [[a]]\n- [[b]]\n\n"
        "## Sources\n\n- [[c]]\n\n"
        "## Kaynaklar\n\n- [[d]]\n"
    )
    chunks = chunk_by_heading([make_doc(body)])
    headings = [c.heading for c in chunks]
    assert "Related" not in headings
    assert "Sources" not in headings
    assert "Kaynaklar" not in headings
    assert "Real Content" in headings


def test_by_heading_merges_sections_shorter_than_the_minimum():
    """A handful of words is too little to embed on its own; short sections
    are folded into the preceding chunk instead."""
    body = f"## Long\n\n{long_section()}\n\n## Tiny\n\nonly three words\n"
    chunks = chunk_by_heading([make_doc(body)])
    assert len(chunks) == 1
    assert "Tiny" in chunks[0].text  # merged, not dropped
    assert "only three words" in chunks[0].text


def test_by_heading_keeps_text_before_the_first_heading():
    body = f"{long_section()}\n\n## Later Section\n\n{long_section()}"
    chunks = chunk_by_heading([make_doc(body)])
    assert len(chunks) == 2
    assert chunks[0].heading is None  # the preamble


def test_by_heading_falls_back_to_whole_document_when_no_headings():
    """Flashcard files rarely use `##`; they must still produce a chunk."""
    body = "Question one?\n?\nAnswer.\n\n---\n\nQuestion two?\n?\nAnswer."
    chunks = chunk_by_heading([make_doc(body)])
    assert len(chunks) == 1
    assert "Question one?" in chunks[0].text
    assert "Question two?" in chunks[0].text


def test_by_heading_produces_unique_chunk_ids():
    body = f"## A\n\n{long_section()}\n\n## B\n\n{long_section()}\n\n## C\n\n{long_section()}"
    chunks = chunk_by_heading([make_doc(body)])
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids))


def test_by_heading_ignores_case_when_dropping_link_sections():
    body = f"## Content\n\n{long_section()}\n\n## RELATED\n\n- [[a]]\n"
    chunks = chunk_by_heading([make_doc(body)])
    assert [c.heading for c in chunks] == ["Content"]


def test_empty_document_produces_no_chunks_from_by_heading():
    chunks = chunk_by_heading([make_doc("")])
    assert chunks == []


# --- fixed_window ---

def test_fixed_window_respects_the_configured_size():
    body = " ".join(str(i) for i in range(FIXED_WINDOW_WORDS * 2))
    chunks = chunk_fixed_window([make_doc(body)])
    assert len(chunks) > 1
    for chunk in chunks:
        # The header prefix adds words, so check the body portion only.
        body_words = chunk.text.split("\n\n", 1)[1].split()
        assert len(body_words) <= FIXED_WINDOW_WORDS


def test_fixed_window_overlaps_consecutive_chunks():
    body = " ".join(str(i) for i in range(FIXED_WINDOW_WORDS + 50))
    chunks = chunk_fixed_window([make_doc(body)])
    assert len(chunks) == 2
    first = set(chunks[0].text.split())
    second = set(chunks[1].text.split())
    shared = first & second
    # Overlap words plus the header tokens; the point is that it is not empty.
    assert len(shared) >= FIXED_WINDOW_OVERLAP


def test_fixed_window_short_document_gives_one_chunk():
    chunks = chunk_fixed_window([make_doc("only a few words here")])
    assert len(chunks) == 1


def test_fixed_window_skips_empty_documents():
    assert chunk_fixed_window([make_doc("")]) == []


# --- shared invariants ---

def test_all_strategies_preserve_document_identity():
    doc = make_doc(f"## One\n\n{long_section()}\n\n## Two\n\n{long_section()}", slug="my-slug")
    for name, fn in CHUNKERS.items():
        for chunk in fn([doc]):
            assert chunk.doc_slug == "my-slug", f"{name} lost the slug"
            assert chunk.doc_path == "concepts/my-slug.md", f"{name} lost the path"
            assert chunk.doc_type == "concept", f"{name} lost the type"


def test_registry_exposes_the_three_strategies():
    assert set(CHUNKERS) == {"whole_doc", "by_heading", "fixed_window"}


# readable_text turns an embedded chunk back into something worth showing a
# reader. It runs on every result the dashboard displays.


def test_readable_text_drops_the_header_the_embedder_needs():
    chunk = {
        "doc_title": "ROC Egrisi ve AUC",
        "text": "ROC Egrisi ve AUC (concept)\ntags: concept, ml\n\nGercek metin burada.",
    }
    assert readable_text(chunk) == "Gercek metin burada."


def test_readable_text_drops_stacked_opening_headings():
    """A whole-document chunk opens with the title and then its first section;
    both are already shown beside the file path."""
    chunk = {
        "doc_title": "ROC Egrisi ve AUC",
        "text": (
            "ROC Egrisi ve AUC (concept)\ntags: concept\n\n"
            "# ROC Egrisi ve AUC\n\n## Tek cumle tanim\n\nROC egrisi tradeoff'u gosterir."
        ),
    }
    assert readable_text(chunk) == "ROC egrisi tradeoff'u gosterir."


def test_readable_text_keeps_headings_that_are_not_at_the_start():
    """Only the opening headings are redundant -- one further in is content."""
    chunk = {"doc_title": "T", "text": "T (concept)\ntags: t\n\nGiris cumlesi.\n\n## Sonra\n\nDevam."}
    assert readable_text(chunk) == "Giris cumlesi. ## Sonra Devam."


def test_readable_text_leaves_a_chunk_without_the_header_alone():
    assert readable_text({"doc_title": "T", "text": "Duz metin, onek yok."}) == "Duz metin, onek yok."


def test_readable_text_truncates_to_the_requested_length():
    chunk = {"doc_title": "T", "text": "T (concept)\ntags: t\n\n" + "kelime " * 100}
    assert len(readable_text(chunk, 40)) == 40


def test_readable_text_survives_a_chunk_that_is_only_headings():
    chunk = {"doc_title": "T", "text": "T (concept)\ntags: t\n\n# Baslik\n\n## Alt baslik\n"}
    assert readable_text(chunk) == ""
