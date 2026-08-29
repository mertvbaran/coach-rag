"""Loads vault markdown files into Document objects."""

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class Document:
    path: str  # "concepts/roc-auc.md", relative to the vault root
    slug: str  # "roc-auc" (filename without extension, the gold-standard join key)
    title: str
    tags: list = field(default_factory=list)
    doc_type: str = ""
    body: str = ""  # content with frontmatter stripped


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Extracts YAML frontmatter from the start of the file only.

    Flashcard files use `---` as a card separator, so a naive split on any
    `^---$` line would cut in the wrong places. Frontmatter is only ever
    the block starting at line 1.
    """
    if not text.startswith("---"):
        return {}, text

    lines = text.split("\n")
    if lines[0].strip() != "---":
        return {}, text

    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        return {}, text

    frontmatter_text = "\n".join(lines[1:end_idx])
    body = "\n".join(lines[end_idx + 1 :])

    try:
        meta = yaml.safe_load(frontmatter_text) or {}
    except yaml.YAMLError:
        meta = {}

    return meta, body


def load_vault(vault_root: Path, dirs: tuple = ("concepts", "sources", "flashcards")) -> list[Document]:
    docs = []
    for dirname in dirs:
        folder = vault_root / dirname
        if not folder.exists():
            continue
        for md_path in sorted(folder.rglob("*.md")):
            text = md_path.read_text(encoding="utf-8")
            meta, body = _parse_frontmatter(text)

            rel_path = md_path.relative_to(vault_root).as_posix()
            slug = md_path.stem

            docs.append(
                Document(
                    path=rel_path,
                    slug=slug,
                    title=meta.get("title", slug),
                    tags=meta.get("tags", []) or [],
                    doc_type=meta.get("type", dirname),
                    body=body.strip(),
                )
            )
    return docs


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import SAMPLE_DIR, VAULT_DIRS, VAULT_ROOT

    docs = load_vault(VAULT_ROOT, VAULT_DIRS)
    print(f"Loaded {len(docs)} files from {VAULT_ROOT}")

    # The file count is only a meaningful sanity check against the real vault
    # this project was built for; the bundled sample data is a 5-file stand-in.
    if VAULT_ROOT == SAMPLE_DIR:
        assert len(docs) == 5, f"Expected 5 sample files, found {len(docs)} — fix before proceeding"
        print("OK — 5 sample files verified")
    else:
        assert len(docs) == 91, f"Expected 91 files, found {len(docs)} — fix before proceeding"
        print("OK — 91 files verified")
    print(f"Sample: {docs[0].path} | slug={docs[0].slug} | title={docs[0].title} | type={docs[0].doc_type}")
