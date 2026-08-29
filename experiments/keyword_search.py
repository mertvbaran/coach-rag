"""TF-IDF keyword search over chunk text -- a non-neural retrieval baseline.

Built to answer one question directly: does the embedding model actually
earn its keep over plain keyword matching on this corpus? scikit-learn's
TfidfVectorizer is used rather than a hand-rolled implementation, the same
way numpy's `@` is used for cosine similarity elsewhere in this project --
TF-IDF itself is a well-understood, single-purpose calculation, not an
orchestration layer that would hide how retrieval works.
"""

from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class KeywordIndex:
    vectorizer: TfidfVectorizer
    matrix: "scipy.sparse.spmatrix"  # noqa: F821 -- type-only reference, avoids importing scipy just for the hint


def build_keyword_index(texts: list[str]) -> KeywordIndex:
    vectorizer = TfidfVectorizer(lowercase=True)
    matrix = vectorizer.fit_transform(texts)
    return KeywordIndex(vectorizer=vectorizer, matrix=matrix)


def keyword_search(query: str, index: KeywordIndex, k: int = 5) -> list[tuple[int, float]]:
    query_vec = index.vectorizer.transform([query])
    scores = cosine_similarity(query_vec, index.matrix)[0]
    top_idx = scores.argsort()[::-1][:k]
    return [(int(i), float(scores[i])) for i in top_idx]


if __name__ == "__main__":
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent))
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    from config import INDEX_DIR
    from store import load_index

    chunks, _ = load_index(INDEX_DIR, "by_heading")
    texts = [c["text"] for c in chunks]
    index = build_keyword_index(texts)

    results = keyword_search("ROC eğrisi neden eşikten bağımsız?", index, k=3)
    for rank, (idx, score) in enumerate(results, start=1):
        print(f"[{rank}] {score:.4f}  {chunks[idx]['doc_slug']} :: {chunks[idx]['heading']}")
