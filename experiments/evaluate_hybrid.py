"""Compares embedding search, keyword search, and a hybrid of the two on the
by_heading index, over the same scored questions evaluate.py uses.

Scores from the two retrievers live on different, incomparable scales
(cosine similarity in [-1, 1] vs. TF-IDF cosine in [0, 1], with very
different typical magnitudes), so each is min-max normalized across the
full candidate set before combining. The hybrid score is a weighted sum;
HYBRID_WEIGHT is the weight on the bi-encoder (embedding) score.

Writes results/hybrid_impact.md and hybrid_impact.tr.md.
"""

import sys
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from config import CACHE_DIR, INDEX_DIR, RESULTS_DIR
from embedder import Embedder
from evaluate import dedupe_by_doc, load_questions
from keyword_search import build_keyword_index
from report import Report, best_cell
from sklearn.metrics.pairwise import cosine_similarity
from store import load_index

CHUNKER = "by_heading"
HYBRID_WEIGHT = 0.5  # weight on the bi-encoder score; (1 - HYBRID_WEIGHT) on TF-IDF
K_VALUES = [1, 3, 5]


def normalize(scores: np.ndarray) -> np.ndarray:
    lo, hi = scores.min(), scores.max()
    if hi - lo < 1e-9:
        return np.zeros_like(scores)
    return (scores - lo) / (hi - lo)


def evaluate_method(name: str, score_fn, chunks: list[dict], questions: list[dict]) -> dict:
    hit_at = {k: [] for k in K_VALUES}
    mrr_values = []

    for q in questions:
        expected = set(q["expected"])
        scores = score_fn(q["question"])
        ranked_docs = dedupe_by_doc(chunks, scores, max(K_VALUES))

        for k in K_VALUES:
            top_k = set(ranked_docs[:k])
            hit_at[k].append(1 if top_k & expected else 0)

        rank = next((i for i, slug in enumerate(ranked_docs, start=1) if slug in expected), None)
        mrr_values.append(1 / rank if rank else 0)

    return {
        "method": name,
        "hit_rate": {k: float(np.mean(hit_at[k])) for k in K_VALUES},
        "mrr": float(np.mean(mrr_values)),
    }


def main():
    questions_path = Path(__file__).parent.parent / "eval" / "questions.yaml"
    questions = [q for q in load_questions(questions_path) if q["expected"]]
    print(f"Loaded {len(questions)} scored questions")

    chunks, embeddings = load_index(INDEX_DIR, CHUNKER)
    texts = [c["text"] for c in chunks]
    keyword_index = build_keyword_index(texts)
    embedder = Embedder(CACHE_DIR)

    def biencoder_scores(question: str) -> np.ndarray:
        query_vec = embedder.embed([question])[0]
        return embeddings @ query_vec

    def tfidf_scores(question: str) -> np.ndarray:
        query_vec = keyword_index.vectorizer.transform([question])
        return cosine_similarity(query_vec, keyword_index.matrix)[0]

    def hybrid_scores(question: str) -> np.ndarray:
        bi = normalize(biencoder_scores(question))
        kw = normalize(tfidf_scores(question))
        return HYBRID_WEIGHT * bi + (1 - HYBRID_WEIGHT) * kw

    results = [
        evaluate_method("bi-encoder only", biencoder_scores, chunks, questions),
        evaluate_method("TF-IDF only", tfidf_scores, chunks, questions),
        evaluate_method(f"hybrid (w={HYBRID_WEIGHT})", hybrid_scores, chunks, questions),
    ]

    for r in results:
        print(f"{r['method']}: HitRate@1={r['hit_rate'][1]:.3f}  HitRate@5={r['hit_rate'][5]:.3f}  MRR={r['mrr']:.3f}")

    # Weight sweep: is 0.5/0.5 just a bad choice, or is TF-IDF unhelpful at any weight?
    sweep = []
    for w in (0.3, 0.5, 0.7, 0.9):
        def scores_at(question: str, w=w) -> np.ndarray:
            bi = normalize(biencoder_scores(question))
            kw = normalize(tfidf_scores(question))
            return w * bi + (1 - w) * kw
        sweep.append(evaluate_method(f"hybrid (w={w})", scores_at, chunks, questions))

    print("\nWeight sweep:")
    for r in sweep:
        print(f"{r['method']}: HitRate@1={r['hit_rate'][1]:.3f}  MRR={r['mrr']:.3f}")

    bi_only, kw_only = results[0], results[1]
    best_hybrid = max(sweep, key=lambda r: r["hit_rate"][1])

    report = Report()
    report.add(
        en="# Hybrid Search: Tested and Rejected\n",
        tr="# Hibrit Arama: Denendi ve Reddedildi\n",
    )
    report.add(
        en=(
            "The system finds sources by meaning: a question and a passage are each "
            "turned into a list of numbers, and the closest ones are returned. That "
            "handles rephrasing well, but can miss an exact term. Keyword search has "
            "the opposite profile — it matches exact words and nothing else.\n\n"
            "Combining the two is standard advice, on the theory that each covers the "
            "other's blind spot. This measures whether it actually helps here.\n"
        ),
        tr=(
            "Sistem kaynakları anlama göre buluyor: soru ve metin parçası birer sayı "
            "dizisine çevriliyor, en yakın olanlar döndürülüyor. Bu yöntem sorunun "
            "farklı kelimelerle sorulmasını iyi kaldırıyor ama bazen tam terimi "
            "kaçırabiliyor. Anahtar kelime araması ise tam tersi: birebir kelime "
            "eşleşmesine bakıyor, başka bir şeye değil.\n\n"
            "İkisini birleştirmek yaygın bir tavsiye — her birinin diğerinin kör "
            "noktasını kapatacağı düşüncesiyle. Buradaki ölçüm, bunun gerçekten işe "
            "yarayıp yaramadığına bakıyor.\n"
        ),
    )
    report.add(
        en=f"Measured on {len(questions)} questions, `{CHUNKER}` index.\n",
        tr=f"{len(questions)} soru üzerinde, `{CHUNKER}` indeksiyle ölçüldü.\n",
    )

    report.add(en="## The three approaches\n", tr="## Üç yaklaşım\n")
    names = {
        "bi-encoder only": ("meaning-based search only", "yalnızca anlama dayalı arama"),
        "TF-IDF only": ("keyword search only", "yalnızca anahtar kelime araması"),
    }
    best_h1_all = max(r["hit_rate"][1] for r in results)
    best_mrr_all = max(r["mrr"] for r in results)

    report.add(
        en="| method | correct source ranked 1st | in top 3 | in top 5 | ranking quality |",
        tr="| yöntem | doğru kaynak 1. sırada | ilk 3'te | ilk 5'te | sıralama kalitesi |",
    )
    report.both("|---|---|---|---|---|")
    for r in sorted(results, key=lambda r: -r["hit_rate"][1]):
        en_name, tr_name = names.get(r["method"], (f"the two mixed evenly", "ikisi eşit karışım"))
        row = (
            f"| {{name}} | {best_cell(r['hit_rate'][1], best_h1_all)} | "
            f"{r['hit_rate'][3]:.3f} | {r['hit_rate'][5]:.3f} | "
            f"{best_cell(r['mrr'], best_mrr_all)} |"
        )
        report.add(en=row.format(name=en_name), tr=row.format(name=tr_name))
    report.add(
        en=(
            f"\nThe first column is the share of questions whose correct source was "
            f"ranked first — the measure that matters most, since people read the top "
            f"result. Meaning-based search reaches {bi_only['hit_rate'][1]:.3f}, "
            f"keyword search {kw_only['hit_rate'][1]:.3f}, and mixing them lands "
            f"below the better of the two rather than above it.\n"
        ),
        tr=(
            f"\nİlk sütun, doğru kaynağın ilk sıraya konduğu soruların oranı — en "
            f"önemli ölçüt bu, çünkü insanlar en üstteki sonucu okuyor. Anlama dayalı "
            f"arama {bi_only['hit_rate'][1]:.3f}, anahtar kelime araması "
            f"{kw_only['hit_rate'][1]:.3f} veriyor; ikisini karıştırmak ise iyi olanın "
            f"üstüne çıkmak yerine altında kalıyor.\n"
        ),
    )

    report.add(
        en="## Does a different mix help?\n",
        tr="## Farklı bir karışım oranı işe yarar mı?\n",
    )
    report.add(
        en=(
            "Weight 1.0 means meaning-based search only; lower values give keyword "
            "search more say.\n"
        ),
        tr=(
            "1.0 ağırlık, yalnızca anlama dayalı arama demek; değer düştükçe anahtar "
            "kelime aramasının payı artıyor.\n"
        ),
    )
    sweep_best_h1 = max([bi_only["hit_rate"][1]] + [r["hit_rate"][1] for r in sweep])
    sweep_best_mrr = max([bi_only["mrr"]] + [r["mrr"] for r in sweep])

    report.add(
        en="| weight on meaning-based search | correct source ranked 1st | in top 3 | in top 5 | ranking quality |",
        tr="| anlama dayalı aramanın ağırlığı | doğru kaynak 1. sırada | ilk 3'te | ilk 5'te | sıralama kalitesi |",
    )
    report.both("|---|---|---|---|---|")
    row_tpl = (
        "| {label} | " + best_cell(bi_only["hit_rate"][1], sweep_best_h1) + " | "
        f"{bi_only['hit_rate'][3]:.3f} | {bi_only['hit_rate'][5]:.3f} | "
        + best_cell(bi_only["mrr"], sweep_best_mrr) + " |"
    )
    report.add(
        en=row_tpl.format(label="1.0 (meaning only)"),
        tr=row_tpl.format(label="1.0 (yalnızca anlam)"),
    )
    for w, r in zip((0.3, 0.5, 0.7, 0.9), sweep):
        report.both(
            f"| {w} | {best_cell(r['hit_rate'][1], sweep_best_h1)} | "
            f"{r['hit_rate'][3]:.3f} | {r['hit_rate'][5]:.3f} | "
            f"{best_cell(r['mrr'], sweep_best_mrr)} |"
        )

    report.add(en="## Why it does not help here\n", tr="## Neden burada işe yaramıyor\n")
    best_w = dict(zip((0.3, 0.5, 0.7, 0.9), sweep))
    best_weight = max(best_w, key=lambda w: best_w[w]["hit_rate"][1])
    report.add(
        en=(
            f"No mix beats meaning-based search on its own. The closest is a weight "
            f"of {best_weight} at {best_hybrid['hit_rate'][1]:.3f}, still short "
            f"of {bi_only['hit_rate'][1]:.3f}.\n\n"
            f"The reason is the corpus. Keyword search earns its place when documents "
            f"contain rare, exact strings — product codes, error numbers, unusual "
            f"names. These notes are the opposite: a few dozen pages that all share "
            f"the same machine-learning vocabulary. Nearly every page mentions "
            f"\"model\", \"veri\", \"metrik\", so matching on those words separates "
            f"almost nothing, and mixing that signal in only dilutes a stronger one.\n\n"
            f"The result was measured, not assumed, and the code was left unchanged: "
            f"`query.py` still uses meaning-based search alone.\n"
        ),
        tr=(
            f"Hiçbir karışım, tek başına anlama dayalı aramayı geçemiyor. En yakını "
            f"{best_weight} ağırlığı ({best_hybrid['hit_rate'][1]:.3f}) ve o da "
            f"{bi_only['hit_rate'][1]:.3f} değerinin altında kalıyor.\n\n"
            f"Sebep, üzerinde çalışılan metinlerin kendisi. Anahtar kelime araması, "
            f"belgelerde nadir ve birebir eşleşen ifadeler olduğunda değer katar — ürün "
            f"kodu, hata numarası, alışılmadık isimler gibi. Buradaki notlar ise tam "
            f"tersi: aynı makine öğrenmesi kelime dağarcığını paylaşan birkaç düzine "
            f"sayfa. Neredeyse her sayfada \"model\", \"veri\", \"metrik\" geçiyor; "
            f"bu kelimelere bakarak eşleşme yapmak neredeyse hiçbir şeyi ayırt "
            f"etmiyor, karışıma eklendiğinde ise güçlü sinyali sulandırıyor.\n\n"
            f"Sonuç varsayılmadı, ölçüldü ve kod değiştirilmedi: `query.py` hâlâ "
            f"yalnızca anlama dayalı aramayı kullanıyor.\n"
        ),
    )

    written = report.write(RESULTS_DIR, "hybrid_impact")
    print("\nWritten:")
    for path in written:
        print(f"  {path}")


if __name__ == "__main__":
    main()
