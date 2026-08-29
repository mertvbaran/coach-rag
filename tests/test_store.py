"""Tests for index persistence and similarity search."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from chunkers import Chunk
from store import load_index, save_index, search


def make_chunks(n: int) -> list[Chunk]:
    return [
        Chunk(
            doc_slug=f"doc-{i}",
            doc_path=f"concepts/doc-{i}.md",
            doc_title=f"Doc {i}",
            doc_type="concept",
            heading=f"Section {i}" if i % 2 else None,
            text=f"content of chunk {i}",
            chunk_id=f"doc-{i}#0",
        )
        for i in range(n)
    ]


def test_save_and_load_round_trip(tmp_path):
    chunks = make_chunks(3)
    embeddings = np.random.rand(3, 8).astype(np.float32)
    save_index(tmp_path, "test", chunks, embeddings)

    loaded_chunks, loaded_emb = load_index(tmp_path, "test")
    assert len(loaded_chunks) == 3
    assert loaded_chunks[0]["doc_slug"] == "doc-0"
    assert loaded_chunks[1]["heading"] == "Section 1"
    assert loaded_chunks[0]["heading"] is None
    np.testing.assert_allclose(loaded_emb, embeddings)


def test_load_index_reports_the_command_that_would_fix_it(tmp_path):
    """A missing index is a normal situation (nothing built yet), so it should
    say what to run rather than surfacing a bare traceback."""
    with pytest.raises(FileNotFoundError) as exc:
        load_index(tmp_path, "by_heading")
    message = str(exc.value)
    assert "by_heading" in message
    assert "build_index.py" in message


def test_load_index_fails_when_only_one_of_the_two_files_exists(tmp_path):
    np.save(tmp_path / "partial.npy", np.zeros((2, 4)))
    with pytest.raises(FileNotFoundError):
        load_index(tmp_path, "partial")


def test_search_ranks_by_cosine_similarity():
    """With L2-normalised vectors the dot product is the cosine, so an aligned
    vector scores 1, an orthogonal one 0, and an opposed one -1."""
    embeddings = np.array([[0.0, 1.0], [1.0, 0.0], [0.0, -1.0]], dtype=np.float32)
    query = np.array([0.0, 1.0], dtype=np.float32)
    results = search(query, embeddings, k=3)

    assert results[0][0] == 0                          # aligned
    assert results[0][1] == pytest.approx(1.0)
    assert results[1][0] == 1                          # orthogonal
    assert results[1][1] == pytest.approx(0.0)
    assert results[2][0] == 2                          # opposed
    assert results[2][1] == pytest.approx(-1.0)


def test_search_returns_at_most_k_results():
    embeddings = np.random.rand(10, 4).astype(np.float32)
    query = np.random.rand(4).astype(np.float32)
    assert len(search(query, embeddings, k=3)) == 3


def test_search_handles_k_larger_than_the_index():
    embeddings = np.random.rand(2, 4).astype(np.float32)
    query = np.random.rand(4).astype(np.float32)
    assert len(search(query, embeddings, k=10)) == 2


def test_search_returns_scores_in_descending_order():
    embeddings = np.random.rand(20, 6).astype(np.float32)
    query = np.random.rand(6).astype(np.float32)
    scores = [score for _, score in search(query, embeddings, k=10)]
    assert scores == sorted(scores, reverse=True)
