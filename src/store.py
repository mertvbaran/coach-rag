"""Save / load / search the embedding matrix and chunk metadata."""

import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from chunkers import Chunk


def save_index(index_dir: Path, name: str, chunks: list[Chunk], embeddings: np.ndarray):
    index_dir.mkdir(parents=True, exist_ok=True)
    np.save(index_dir / f"{name}.npy", embeddings)
    with open(index_dir / f"{name}.jsonl", "w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(asdict(chunk), ensure_ascii=False) + "\n")


def load_index(index_dir: Path, name: str) -> tuple[list[dict], np.ndarray]:
    npy_path = index_dir / f"{name}.npy"
    jsonl_path = index_dir / f"{name}.jsonl"
    if not npy_path.exists() or not jsonl_path.exists():
        raise FileNotFoundError(
            f"No index named '{name}' in {index_dir}. Run "
            f"`python src/build_index.py --chunker {name}` first."
        )

    embeddings = np.load(npy_path)
    chunks = []
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            chunks.append(json.loads(line))
    return chunks, embeddings


def search(query_vec: np.ndarray, embeddings: np.ndarray, k: int = 5) -> list[tuple[int, float]]:
    """Assumes query_vec and embeddings are L2-normalized, so cosine similarity
    reduces to a dot product."""
    scores = embeddings @ query_vec
    top_idx = np.argsort(-scores)[:k]
    return [(int(i), float(scores[i])) for i in top_idx]
