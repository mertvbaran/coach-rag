"""CLI: question -> bi-encoder retrieval -> cross-encoder confidence gate only.

Note: retrieval only, no generation. Foundry Local's chat model is
available (see embedder.py's docstring) but generation was intentionally
left out of scope for the evaluation — see the README's "Retrieval-only
evaluation" section for the rationale.

Re-ranking and out-of-scope detection are deliberately kept as two
separate mechanisms, not one. See reranker.py: a cross-encoder separates
in-scope from out-of-scope questions almost perfectly, but using the same
model to re-rank results hurts ranking quality (HitRate@1 on the
by_heading index drops from 0.809 to 0.596 — see results/rerank_impact.md).
So bi-encoder ranking is left untouched, and the cross-encoder is used
only to decide whether to show a confidence warning.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import CACHE_DIR, INDEX_DIR, TOP_K
from embedder import Embedder
from reranker import CE_OUT_OF_SCOPE_THRESHOLD, Reranker
from store import load_index, search

RERANK_POOL_SIZE = 10  # number of candidates sent to the cross-encoder for the scope check

# The vault mixes Turkish text with mathematical symbols, and the default
# Windows console encoding cannot represent all of them. Without this,
# printing a chunk containing e.g. "≠" raises UnicodeEncodeError mid-result.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("question", type=str)
    # Defaults to by_heading: it wins on HitRate@1 and MRR (results/chunking.md),
    # and the confidence gate's threshold is calibrated against its score
    # distribution -- the same cutoff misbehaves on the other indexes.
    parser.add_argument("--chunker", default="by_heading")
    parser.add_argument("--k", type=int, default=TOP_K)
    parser.add_argument("--no-scope-check", action="store_true", help="skip the cross-encoder confidence gate")
    args = parser.parse_args()

    chunks, embeddings = load_index(INDEX_DIR, args.chunker)

    embedder = Embedder(CACHE_DIR)
    query_vec = embedder.embed([args.question])[0]

    print(f"\nQuestion: {args.question}\n")

    results = search(query_vec, embeddings, k=args.k)

    if not args.no_scope_check:
        pool = search(query_vec, embeddings, k=RERANK_POOL_SIZE)
        pool_texts = [chunks[idx]["text"] for idx, _ in pool]

        reranker = Reranker()
        in_scope, ce_top_score = reranker.is_in_scope(args.question, pool_texts)

        if not in_scope:
            print(f"This isn't covered in my notes (cross-encoder confidence {ce_top_score:.2f}, threshold {CE_OUT_OF_SCOPE_THRESHOLD}).")
            print("Closest matches below, shown with low confidence (bi-encoder ranking):\n")

    print(f"Top {len(results)} sources ({args.chunker} index):\n")
    for rank, (idx, score) in enumerate(results, start=1):
        chunk = chunks[idx]
        heading = f" > {chunk['heading']}" if chunk.get("heading") else ""
        print(f"[{rank}] {chunk['doc_path']}{heading}  (score: {score:.4f})")
        preview = chunk["text"].replace("\n", " ")[:150]
        print(f"    {preview}...")
        print()


if __name__ == "__main__":
    main()
