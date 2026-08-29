"""Helpers for writing measurement reports in both English and Turkish.

The dashboard shows these reports next to a language toggle, so each one is
written twice: `<name>.md` in English and `<name>.tr.md` in Turkish. A reader
sees one or the other, never both.

Numbers are computed once and formatted into whichever language is being
written, so the two versions cannot drift apart in their figures -- only the
prose differs.
"""

from pathlib import Path

LANGUAGES = ("en", "tr")


class Report:
    """Collects lines for both language versions of one report.

    Call `add` with a piece of text per language, or `both` for content that is
    language-independent (tables of numbers, code identifiers). `write` then
    saves one file per language.
    """

    def __init__(self) -> None:
        self._lines: dict[str, list[str]] = {lang: [] for lang in LANGUAGES}

    def add(self, *, en: str, tr: str) -> None:
        """Adds a paragraph, given separately in each language."""
        self._lines["en"].append(en)
        self._lines["tr"].append(tr)

    def both(self, line: str) -> None:
        """Adds the same line to every language -- for tables and identifiers."""
        for lang in LANGUAGES:
            self._lines[lang].append(line)

    def write(self, results_dir: Path, name: str) -> list[Path]:
        """Writes `<name>.md` (English) and `<name>.tr.md` (Turkish)."""
        results_dir.mkdir(exist_ok=True)
        written = []
        for lang in LANGUAGES:
            suffix = ".md" if lang == "en" else ".tr.md"
            path = results_dir / f"{name}{suffix}"
            path.write_text("\n".join(self._lines[lang]), encoding="utf-8")
            written.append(path)
        return written


def best_cell(value: float, best: float, higher_is_better: bool = True, fmt: str = ".3f") -> str:
    """Formats a table cell, bolding it when it is the best in its column.

    Tables of near-identical decimals are hard to read at a glance; bolding
    the winner lets the eye find it without comparing every digit. Markdown's
    own emphasis does this without adding a symbol that has to be explained
    the first time a reader sees it. `higher_is_better=False` is for columns
    like error counts.
    """
    del higher_is_better  # caller decides what "best" is; kept for call-site clarity
    marked = abs(value - best) < 1e-9
    return f"**{value:{fmt}}**" if marked else f"{value:{fmt}}"


def mark_if(value: str, condition: bool) -> str:
    """Bolds a non-numeric cell when it is the notable one in its column."""
    return f"**{value}**" if condition else value


def arrow(before: float, after: float, tolerance: float = 0.005) -> str:
    """Direction of a before/after change, for tables that report both.

    Reading two decimals side by side and working out which way they moved is
    slow; a plain-text arrow makes the direction immediate without an emoji
    that renders inconsistently across fonts and reads as decoration rather
    than data.
    """
    if after - before > tolerance:
        return "↑"
    if before - after > tolerance:
        return "↓"
    return "→"
