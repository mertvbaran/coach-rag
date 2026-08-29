"""Records gate decisions the user marked as wrong, for later recalibration.

The out-of-scope threshold is fitted on a fixed set of questions (see
calibrate_threshold.py). That set is written by hand and is therefore only a
guess at what gets asked in practice -- the bug that prompted this whole
line of work was found by asking a question nobody had thought to include.

This module lets real corrections accumulate instead: when the gate refuses
a question the vault does cover, or accepts one it does not, that question
is appended to a JSONL file with the label it should have had. Recalibration
can then draw on questions that were actually asked rather than only on
invented ones.

The file lives under data/ and is gitignored -- it contains real questions
about the vault's contents, which stay local like the rest of the vault data.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

FEEDBACK_FILENAME = "gate_feedback.jsonl"


def feedback_path(data_dir: Path) -> Path:
    return data_dir / FEEDBACK_FILENAME


def record(data_dir: Path, question: str, ce_score: float, threshold: float,
           gate_said_in_scope: bool, chunker: str) -> Path:
    """Appends one correction. The correct label is the opposite of what the
    gate decided -- this is only called when the user reports a mistake."""
    path = feedback_path(data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "question": question,
        "ce_score": ce_score,
        "threshold_at_the_time": threshold,
        "gate_said_in_scope": gate_said_in_scope,
        "should_be_in_scope": not gate_said_in_scope,
        "chunker": chunker,
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return path


def load(data_dir: Path) -> list[dict]:
    """Returns recorded corrections, most recent last. Empty if none yet.

    If the same question was corrected more than once, only the latest entry
    is kept -- a later correction supersedes an earlier one.
    """
    path = feedback_path(data_dir)
    if not path.exists():
        return []
    by_question: dict[str, dict] = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue  # skip a partially-written line rather than failing
            by_question[entry["question"]] = entry
    return list(by_question.values())


def summary(data_dir: Path) -> str:
    entries = load(data_dir)
    if not entries:
        return "No gate corrections recorded yet."
    should_accept = sum(1 for e in entries if e["should_be_in_scope"])
    should_refuse = len(entries) - should_accept
    return (
        f"{len(entries)} correction(s) recorded: {should_refuse} question(s) that "
        f"should have been refused, {should_accept} that should have been answered."
    )


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import DATA_DIR

    print(summary(DATA_DIR))
    for e in load(DATA_DIR):
        label = "should be answered" if e["should_be_in_scope"] else "should be refused"
        print(f"  [{e['timestamp']}] {label:20} (score {e['ce_score']:.2f})  {e['question']}")
