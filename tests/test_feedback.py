"""Tests for recording and reading back gate corrections."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from feedback import feedback_path, load, record, summary


def test_no_feedback_file_reads_as_empty(tmp_path):
    assert load(tmp_path) == []
    assert "No gate corrections" in summary(tmp_path)


def test_recording_a_refusal_that_should_have_been_answered(tmp_path):
    record(tmp_path, "Bir soru?", -4.5, -3.94, gate_said_in_scope=False, chunker="by_heading")
    entries = load(tmp_path)
    assert len(entries) == 1
    assert entries[0]["question"] == "Bir soru?"
    assert entries[0]["gate_said_in_scope"] is False
    assert entries[0]["should_be_in_scope"] is True   # the correction inverts it
    assert entries[0]["ce_score"] == -4.5


def test_recording_an_answer_that_should_have_been_refused(tmp_path):
    record(tmp_path, "Alakasız soru?", -1.0, -3.94, gate_said_in_scope=True, chunker="by_heading")
    entry = load(tmp_path)[0]
    assert entry["should_be_in_scope"] is False


def test_multiple_corrections_accumulate(tmp_path):
    record(tmp_path, "Soru bir?", -4.0, -3.94, False, "by_heading")
    record(tmp_path, "Soru iki?", -1.0, -3.94, True, "by_heading")
    assert len(load(tmp_path)) == 2


def test_recorrecting_the_same_question_supersedes_the_earlier_entry(tmp_path):
    record(tmp_path, "Aynı soru?", -4.0, -3.94, False, "by_heading")
    record(tmp_path, "Aynı soru?", -4.0, -3.94, True, "by_heading")
    entries = load(tmp_path)
    assert len(entries) == 1
    assert entries[0]["should_be_in_scope"] is False  # the later correction wins


def test_a_corrupt_line_does_not_break_reading_the_rest(tmp_path):
    record(tmp_path, "İyi kayıt?", -4.0, -3.94, False, "by_heading")
    with open(feedback_path(tmp_path), "a", encoding="utf-8") as f:
        f.write("{ this is not valid json\n")
    record(tmp_path, "Başka kayıt?", -2.0, -3.94, True, "by_heading")

    entries = load(tmp_path)
    assert len(entries) == 2  # the broken line is skipped, not fatal


def test_summary_counts_both_directions(tmp_path):
    record(tmp_path, "a?", -4.0, -3.94, gate_said_in_scope=False, chunker="by_heading")
    record(tmp_path, "b?", -4.1, -3.94, gate_said_in_scope=False, chunker="by_heading")
    record(tmp_path, "c?", -1.0, -3.94, gate_said_in_scope=True, chunker="by_heading")
    text = summary(tmp_path)
    assert "3 correction" in text
    assert "1 question(s) that should have been refused" in text
    assert "2 that should have been answered" in text


def test_entries_are_valid_jsonl(tmp_path):
    record(tmp_path, "Türkçe karakterli soru: ğüşiöç?", -3.0, -3.94, False, "by_heading")
    raw = feedback_path(tmp_path).read_text(encoding="utf-8").strip()
    parsed = json.loads(raw)
    assert parsed["question"] == "Türkçe karakterli soru: ğüşiöç?"
    assert "timestamp" in parsed
