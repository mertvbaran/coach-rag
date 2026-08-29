"""Tests for frontmatter parsing and vault loading."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from loader import Document, _parse_frontmatter, load_vault


def test_parses_frontmatter_and_strips_it_from_body():
    text = "---\ntitle: Test\ntags: [a, b]\ntype: concept\n---\n\n# Heading\n\nBody text."
    meta, body = _parse_frontmatter(text)
    assert meta["title"] == "Test"
    assert meta["tags"] == ["a", "b"]
    assert meta["type"] == "concept"
    assert "title:" not in body
    assert "# Heading" in body


def test_file_without_frontmatter_is_returned_unchanged():
    text = "# Just a heading\n\nSome text."
    meta, body = _parse_frontmatter(text)
    assert meta == {}
    assert body == text


def test_flashcard_separators_are_not_mistaken_for_frontmatter():
    """Flashcard files use `---` between cards. A naive split on any `^---$`
    would cut in the wrong place and drop most of the file. Frontmatter is
    only ever the block starting at line 1."""
    text = (
        "---\ntitle: Cards\ntype: flashcard\n---\n\n"
        "Question one?\n?\nAnswer one.\n\n---\n\n"
        "Question two?\n?\nAnswer two.\n\n---\n\n"
        "Question three?\n?\nAnswer three.\n"
    )
    meta, body = _parse_frontmatter(text)
    assert meta["type"] == "flashcard"
    # All three cards must survive; the separators stay in the body.
    assert "Question one?" in body
    assert "Question two?" in body
    assert "Question three?" in body
    assert body.count("---") == 2


def test_frontmatter_not_at_line_one_is_not_parsed():
    text = "Some preamble\n---\ntitle: Not frontmatter\n---\nBody"
    meta, body = _parse_frontmatter(text)
    assert meta == {}
    assert body == text


def test_unterminated_frontmatter_returns_text_unchanged():
    text = "---\ntitle: Broken\nno closing delimiter"
    meta, body = _parse_frontmatter(text)
    assert meta == {}
    assert body == text


def test_malformed_yaml_does_not_raise():
    text = "---\ntitle: [unclosed\n---\n\nBody"
    meta, body = _parse_frontmatter(text)
    assert meta == {}  # falls back rather than crashing
    assert "Body" in body


def test_load_vault_reads_files_and_derives_slug(tmp_path):
    concepts = tmp_path / "concepts"
    concepts.mkdir()
    (concepts / "my-topic.md").write_text(
        "---\ntitle: My Topic\ntype: concept\ntags: [x]\n---\n\nContent here.",
        encoding="utf-8",
    )
    docs = load_vault(tmp_path, ("concepts",))
    assert len(docs) == 1
    doc = docs[0]
    assert doc.slug == "my-topic"          # filename without extension
    assert doc.path == "concepts/my-topic.md"
    assert doc.title == "My Topic"
    assert doc.doc_type == "concept"
    assert doc.body == "Content here."


def test_load_vault_falls_back_to_slug_when_title_missing(tmp_path):
    concepts = tmp_path / "concepts"
    concepts.mkdir()
    (concepts / "untitled-page.md").write_text("No frontmatter at all.", encoding="utf-8")
    docs = load_vault(tmp_path, ("concepts",))
    assert docs[0].title == "untitled-page"
    assert docs[0].doc_type == "concepts"  # falls back to the directory name


def test_load_vault_skips_missing_directories(tmp_path):
    (tmp_path / "concepts").mkdir()
    (tmp_path / "concepts" / "a.md").write_text("x", encoding="utf-8")
    # "sources" does not exist -- must not raise
    docs = load_vault(tmp_path, ("concepts", "sources"))
    assert len(docs) == 1


def test_load_vault_reads_nested_directories(tmp_path):
    nested = tmp_path / "sources" / "courses"
    nested.mkdir(parents=True)
    (nested / "deep.md").write_text("---\ntitle: Deep\n---\nbody", encoding="utf-8")
    docs = load_vault(tmp_path, ("sources",))
    assert len(docs) == 1
    assert docs[0].path == "sources/courses/deep.md"
