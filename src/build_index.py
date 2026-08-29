"""CLI: load the vault -> chunk -> embed -> save an index."""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from chunkers import CHUNKERS
from config import CACHE_DIR, INDEX_DIR, VAULT_DIRS, VAULT_ROOT
from embedder import Embedder
from loader import load_vault
from store import save_index


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--chunker", choices=list(CHUNKERS.keys()), required=True)
    args = parser.parse_args()

    print(f"Loading vault: {VAULT_ROOT}")
    docs = load_vault(VAULT_ROOT, VAULT_DIRS)
    print(f"Loaded {len(docs)} files")

    chunk_fn = CHUNKERS[args.chunker]
    chunks = chunk_fn(docs)
    print(f"'{args.chunker}' produced {len(chunks)} chunks")

    embedder = Embedder(CACHE_DIR)
    texts = [c.text for c in chunks]

    t0 = time.time()
    embeddings = embedder.embed(texts)
    elapsed = time.time() - t0
    print(f"Embedding done in {elapsed:.2f}s (shape: {embeddings.shape})")
    if embedder.truncated_count:
        print(f"Warning: {embedder.truncated_count} chunk(s) were truncated to fit the model's context limit")

    save_index(INDEX_DIR, args.chunker, chunks, embeddings)
    print(f"Saved to {INDEX_DIR}/{args.chunker}.npy + .jsonl")


if __name__ == "__main__":
    main()
