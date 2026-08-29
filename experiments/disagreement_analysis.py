"""Ranks every eval question by where the first correct source landed, and
inspects the worst cases in detail.

This is not another metrics table -- evaluate.py already produces those. The
point here is qualitative: for the questions where retrieval disagreed most
with the gold standard, look at what was actually returned and why.

Writes results/disagreement_analysis.md and disagreement_analysis.tr.md.
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
from report import Report
from store import load_index

CHUNKER = "by_heading"
WORST_N = 5
SHOW_TOP = 3  # chunks shown per question in the report


def ordinal_en(n: int) -> str:
    """1 -> '1st', 2 -> '2nd', 12 -> '12th'."""
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def rank_of(ranked_docs: list[str], expected: set[str]) -> int | None:
    for i, slug in enumerate(ranked_docs, start=1):
        if slug in expected:
            return i
    return None


def main():
    questions_path = Path(__file__).parent.parent / "eval" / "questions.yaml"
    questions = load_questions(questions_path)
    scored = [q for q in questions if q["expected"]]

    embedder = Embedder(CACHE_DIR)
    chunks, embeddings = load_index(INDEX_DIR, CHUNKER)

    rows = []
    for q in scored:
        expected = set(q["expected"])
        query_vec = embedder.embed([q["question"]])[0]
        scores = embeddings @ query_vec
        ranked_docs = dedupe_by_doc(chunks, scores, len(chunks))
        rank = rank_of(ranked_docs, expected)
        mrr = 1 / rank if rank else 0

        top_idx = np.argsort(-scores)[:SHOW_TOP]
        top_chunks = [(chunks[i]["doc_slug"], chunks[i]["heading"], float(scores[i])) for i in top_idx]

        rows.append({
            "id": q["id"],
            "question": q["question"],
            "type": q["type"],
            "expected": sorted(expected),
            "rank": rank,
            "mrr": mrr,
            "top_chunks": top_chunks,
        })

    rows.sort(key=lambda r: r["mrr"])
    worst = rows[:WORST_N]

    print(f"Worst {WORST_N} of {len(rows)} questions by reciprocal rank ({CHUNKER} index):\n")
    for r in worst:
        print(f"[{r['id']}] MRR={r['mrr']:.2f} rank={r['rank']} type={r['type']}")
        print(f"  Q: {r['question']}")
        print(f"  expected: {r['expected']}")
        for slug, heading, score in r["top_chunks"]:
            print(f"    {score:.4f}  {slug} :: {heading}")
        print()

    perfect = [r for r in rows if r["rank"] == 1]
    imperfect = [r for r in rows if r["rank"] != 1]

    report = Report()
    report.add(
        en="# Where the Search Gets It Wrong\n",
        tr="# Aramanın Yanıldığı Yerler\n",
    )
    report.add(
        en=(
            "A single accuracy figure says how often the search is right, not where "
            "it goes wrong. This report takes every test question, checks how far "
            "down the list the correct source appeared, and looks closely at the "
            "ones it ranked worst — those are where the interesting failures are.\n"
        ),
        tr=(
            "Tek bir başarı yüzdesi, aramanın ne sıklıkla doğru bulduğunu söyler; "
            "nerede yanıldığını söylemez. Bu rapor her test sorusunu alıp doğru "
            "kaynağın listenin kaçıncı sırasında çıktığına bakıyor ve en kötü "
            "sıraladıklarını yakından inceliyor — ilginç hatalar orada.\n"
        ),
    )
    report.add(
        en=(
            f"Of {len(rows)} test questions, {len(perfect)} put a correct source "
            f"first. The {len(imperfect)} that did not are examined below.\n"
        ),
        tr=(
            f"{len(rows)} test sorusundan {len(perfect)} tanesinde doğru kaynak ilk "
            f"sırada çıktı. Çıkmayan {len(imperfect)} soru aşağıda inceleniyor.\n"
        ),
    )

    report.add(
        en="## Two patterns behind most of the mistakes\n",
        tr="## Hataların çoğunun ardındaki iki örüntü\n",
    )
    report.add(
        en=(
            "**A page can sound like the answer without being it.** When a question "
            "describes a symptom instead of naming the concept, the search often "
            "lands on pages that share the phrasing but not the subject. Asking what "
            "explains a model that does well in training and badly in production "
            "brings up the pages about imbalanced data — they are full of "
            "\"looks good on one measure, fails in practice\" language — ahead of the "
            "section that actually covers overfitting.\n\n"
            "**Broad pages crowd out specific ones.** Several questions rank a wide "
            "course summary above the short page written about exactly that concept. "
            "The summary mentions the term among many others, so it matches a little "
            "on everything; the focused page matches strongly on one thing. At the "
            "very top of the list, breadth sometimes wins.\n\n"
            "Neither is a bug with a fix. Both follow from comparing whole passages "
            "at once, and knowing about them sets a realistic expectation of what "
            "this search will and will not get right.\n"
        ),
        tr=(
            "**Bir sayfa, cevap olmadan cevap gibi durabilir.** Soru kavramın adını "
            "vermek yerine bir belirtiyi tarif ettiğinde, arama çoğu zaman aynı "
            "ifadeyi paylaşan ama konusu farklı sayfalara gidiyor. Eğitimde iyi, "
            "gerçek veride kötü sonuç veren bir modelin nedenini sorduğunuzda, "
            "dengesiz veri setleriyle ilgili sayfalar öne çıkıyor — çünkü onlar "
            "\"bir ölçüte göre iyi görünüyor ama pratikte başarısız\" diline sahip — "
            "ve asıl overfitting'i anlatan bölümün önüne geçiyorlar.\n\n"
            "**Geniş kapsamlı sayfalar, özel sayfaların önüne geçiyor.** Bazı "
            "sorularda geniş bir ders özeti, tam o kavram için yazılmış kısa sayfanın "
            "üstünde çıkıyor. Ders özeti terimi diğer birçok terimle birlikte "
            "andığından her şeye biraz benziyor; odaklı sayfa ise tek bir şeye çok "
            "benziyor. Listenin en tepesinde bazen genişlik kazanıyor.\n\n"
            "İkisi de düzeltilecek bir hata değil. Her ikisi de metinleri bütün "
            "olarak karşılaştırmanın doğal sonucu; bunları bilmek, bu aramanın neyi "
            "doğru bulup neyi bulamayacağına dair gerçekçi bir beklenti veriyor.\n"
        ),
    )

    # The question set labels each question by what it tests. Spelled out, since
    # the raw tags mean nothing to a reader who has not seen the question file.
    types_en = {
        "direct": "asked using the same words as the notes",
        "paraphrase": "asked in different words than the notes use",
        "multi_doc": "needs more than one source",
        "code_switch": "mixes Turkish and English terms",
    }
    types_tr = {
        "direct": "notlardaki terimlerle soruldu",
        "paraphrase": "notlardan farklı kelimelerle soruldu",
        "multi_doc": "birden fazla kaynak gerektiriyor",
        "code_switch": "Türkçe ve İngilizce terimler karışık",
    }

    def render(r: dict) -> None:
        rank = r["rank"]
        report.add(
            en=(
                f"### The right page was {ordinal_en(rank)} in the list "
                f"— {types_en.get(r['type'], r['type'])}\n"
            ),
            tr=(
                f"### Doğru sayfa listenin {rank}. sırasındaydı "
                f"— {types_tr.get(r['type'], r['type'])}\n"
            ),
        )
        report.add(en=f"**Question:** {r['question']}  ", tr=f"**Soru:** {r['question']}  ")
        report.add(
            en=f"**Expected source:** {', '.join(r['expected'])}\n",
            tr=f"**Beklenen kaynak:** {', '.join(r['expected'])}\n",
        )
        report.add(
            en="| score | page | section |",
            tr="| skor | sayfa | bölüm |",
        )
        report.both("|---|---|---|")
        for slug, heading, score in r["top_chunks"]:
            marker_en = " **&larr; expected**" if slug in r["expected"] else ""
            marker_tr = " **&larr; beklenen**" if slug in r["expected"] else ""
            report.add(
                en=f"| {score:.4f} | {slug} | {heading}{marker_en} |",
                tr=f"| {score:.4f} | {slug} | {heading}{marker_tr} |",
            )
        report.both("")

    report.add(
        en="## The questions it ranked worst\n",
        tr="## En kötü sıraladığı sorular\n",
    )
    if imperfect:
        report.add(
            en="Worst first. Only the top 3 results are shown for each.\n",
            tr="En kötüden başlayarak. Her soru için yalnızca ilk 3 sonuç gösteriliyor.\n",
        )
        for r in imperfect:
            render(r)
    else:
        report.add(
            en="None — every question ranked a correct source first.\n",
            tr="Yok — her soruda doğru kaynak ilk sırada çıktı.\n",
        )

    report.add(
        en="## The questions it got right\n",
        tr="## Doğru bulduğu sorular\n",
    )
    report.add(
        en=f"Listed without detail. All {len(perfect)} ranked a correct source first.\n",
        tr=f"Ayrıntısız liste. {len(perfect)} sorunun hepsinde doğru kaynak ilk sırada.\n",
    )
    report.add(en="| question | how it was asked |", tr="| soru | nasıl soruldu |")
    report.both("|---|---|")
    for r in perfect:
        report.add(
            en=f"| {r['question']} | {types_en.get(r['type'], r['type'])} |",
            tr=f"| {r['question']} | {types_tr.get(r['type'], r['type'])} |",
        )
    report.both("")

    written = report.write(RESULTS_DIR, "disagreement_analysis")
    print("\nWritten:")
    for p in written:
        print(f"  {p}")


if __name__ == "__main__":
    main()
