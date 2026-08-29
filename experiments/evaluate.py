"""CLI: eval/questions.yaml -> retrieval metrics per chunker -> results/chunking.md"""

import sys
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from config import CACHE_DIR, INDEX_DIR, RESULTS_DIR
from embedder import Embedder
from report import Report, best_cell
from store import load_index

K_VALUES = [1, 3, 5, 10]
EVAL_K = 5  # the k used for the main comparison table


def load_questions(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["questions"]


def dedupe_by_doc(chunks: list[dict], scores: np.ndarray, k: int) -> list[str]:
    """Returns the top-k distinct doc_slugs by best chunk score."""
    order = np.argsort(-scores)
    seen = []
    for idx in order:
        slug = chunks[idx]["doc_slug"]
        if slug not in seen:
            seen.append(slug)
        if len(seen) >= k:
            break
    return seen


def evaluate_chunker(chunker_name: str, questions: list[dict], embedder: Embedder) -> dict:
    chunks, embeddings = load_index(INDEX_DIR, chunker_name)

    hit_at = {k: [] for k in K_VALUES}
    recall_at = {k: [] for k in K_VALUES}
    precision_at = {k: [] for k in K_VALUES}
    mrr_values = []

    max_k = max(K_VALUES)

    for q in questions:
        expected = set(q["expected"])
        if not expected:
            continue  # out-of-scope questions are excluded from recall/MRR, reported separately

        query_vec = embedder.embed([q["question"]])[0]
        scores = embeddings @ query_vec
        ranked_docs = dedupe_by_doc(chunks, scores, max_k)

        for k in K_VALUES:
            top_k = set(ranked_docs[:k])
            hit = 1 if top_k & expected else 0
            hit_at[k].append(hit)
            recall_at[k].append(len(top_k & expected) / len(expected))
            precision_at[k].append(len(top_k & expected) / k)

        rank = None
        for i, slug in enumerate(ranked_docs, start=1):
            if slug in expected:
                rank = i
                break
        mrr_values.append(1 / rank if rank else 0)

    n = len(mrr_values)
    return {
        "chunker": chunker_name,
        "n_chunks": len(chunks),
        "n_questions": n,
        "hit_rate": {k: np.mean(hit_at[k]) for k in K_VALUES},
        "recall": {k: np.mean(recall_at[k]) for k in K_VALUES},
        "precision": {k: np.mean(precision_at[k]) for k in K_VALUES},
        "mrr": np.mean(mrr_values),
    }


def evaluate_out_of_scope(chunker_name: str, questions: list[dict], embedder: Embedder, threshold: float = 0.3) -> dict:
    """Checks whether the top score for out-of-scope questions stays below the threshold."""
    chunks, embeddings = load_index(INDEX_DIR, chunker_name)
    oos = [q for q in questions if not q["expected"]]
    below_threshold = 0
    for q in oos:
        query_vec = embedder.embed([q["question"]])[0]
        scores = embeddings @ query_vec
        top_score = float(np.max(scores))
        if top_score < threshold:
            below_threshold += 1
    return {"n_oos": len(oos), "below_threshold": below_threshold, "threshold": threshold}


def main():
    questions_path = Path(__file__).parent.parent / "eval" / "questions.yaml"
    questions = load_questions(questions_path)
    print(f"Loaded {len(questions)} questions")

    embedder = Embedder(CACHE_DIR)

    chunkers = ["whole_doc", "by_heading", "fixed_window"]
    available = [c for c in chunkers if (INDEX_DIR / f"{c}.npy").exists()]
    print(f"Evaluating indexes: {available}")

    results = []
    oos_results = []
    for chunker_name in available:
        print(f"\n=== {chunker_name} ===")
        res = evaluate_chunker(chunker_name, questions, embedder)
        results.append(res)
        oos = evaluate_out_of_scope(chunker_name, questions, embedder)
        oos_results.append((chunker_name, oos))
        print(f"HitRate@5={res['hit_rate'][5]:.3f}  Recall@5={res['recall'][5]:.3f}  MRR={res['mrr']:.3f}")

    n_scored = sum(1 for q in questions if q["expected"])
    n_oos = sum(1 for q in questions if not q["expected"])

    report = Report()
    report.add(
        en="# Chunking Strategy Comparison\n",
        tr="# Chunking Stratejisi Karşılaştırması\n",
    )
    report.add(
        en=(
            "How a document is split before embedding decides what the retriever "
            "can find. Three strategies are compared here on the same questions:\n\n"
            "- **`whole_doc`** — treats each file as a single chunk.\n"
            "- **`by_heading`** — splits on markdown `## ` headings.\n"
            "- **`fixed_window`** — cuts every 300 words with no regard for "
            "structure. The floor of the comparison: it is here to show whether "
            "using structure buys anything at all.\n"
        ),
        tr=(
            "Bir dokümanın embedding öncesinde nasıl parçalandığı, arama sisteminin "
            "neyi bulabileceğini belirler. Burada üç strateji aynı sorular üzerinde "
            "karşılaştırılıyor:\n\n"
            "- **`whole_doc`** — her dosyayı tek bir chunk sayar.\n"
            "- **`by_heading`** — markdown `## ` başlıklarından böler.\n"
            "- **`fixed_window`** — belgenin yapısına hiç bakmadan her 300 kelimede "
            "bir keser. Karşılaştırmanın alt sınırı: yapı bilgisi kullanmanın gerçekten "
            "bir fark yaratıp yaratmadığını görmek için burada.\n"
        ),
    )
    report.add(
        en=(
            f"Measured on {len(questions)} gold-standard questions ({n_scored} with "
            f"an expected source, {n_oos} deliberately out of scope). Questions and "
            f"expected answers are in `eval/questions.yaml`.\n"
        ),
        tr=(
            f"Ölçüm {len(questions)} soruluk gold-standard set üzerinde yapıldı: "
            f"{n_scored} sorunun beklenen bir kaynağı var, {n_oos} tanesi ise "
            f"bilerek kapsam dışı seçildi. Sorular ve beklenen cevaplar "
            f"`eval/questions.yaml` dosyasında.\n"
        ),
    )

    report.add(en="## Results\n", tr="## Sonuçlar\n")
    report.add(
        en=(
            "Ordered best to worst by how often the correct source is ranked first. "
            "The best value in each column is in **bold**.\n"
        ),
        tr=(
            "Doğru kaynağı ilk sıraya koyma başarısına göre iyiden kötüye sıralı. "
            "Her sütunun en iyi değeri **koyu renkte** gösteriliyor.\n"
        ),
    )

    ranked = sorted(results, key=lambda r: -r["hit_rate"][1])
    winners = {
        "h1": max(r["hit_rate"][1] for r in results),
        "h5": max(r["hit_rate"][5] for r in results),
        "recall": max(r["recall"][5] for r in results),
        "precision": max(r["precision"][5] for r in results),
        "mrr": max(r["mrr"] for r in results),
    }

    cell = best_cell

    report.add(
        en="| chunker | pieces | correct source ranked 1st | found in top 5 | all sources in top 5 | of 5 shown, share correct | ranking quality |",
        tr="| chunker | parça | doğru kaynak 1. sırada | ilk 5'te bulundu | tüm kaynaklar ilk 5'te | 5 sonuçtan doğru oranı | sıralama kalitesi |",
    )
    report.both("|---|---|---|---|---|---|---|")
    for res in ranked:
        name = res["chunker"]
        label = f"**{name}**" if name == "by_heading" else name
        report.both(
            f"| {label} | {res['n_chunks']} | "
            f"{cell(res['hit_rate'][1], winners['h1'])} | "
            f"{cell(res['hit_rate'][5], winners['h5'])} | "
            f"{cell(res['recall'][5], winners['recall'])} | "
            f"{cell(res['precision'][5], winners['precision'])} | "
            f"{cell(res['mrr'], winners['mrr'])} |"
        )

    report.add(
        en=(
            "\n**What the columns mean.** All values run from 0 to 1, higher is "
            "better.\n\n"
            "- **correct source ranked 1st** — how often the very first result was "
            "right. The strictest measure, and the one that matters most in practice: "
            "people read the top result. *(HitRate@1)*\n"
            "- **found in top 5** — how often a correct source appeared anywhere in "
            "the five results shown. *(HitRate@5)*\n"
            "- **all sources in top 5** — some questions have more than one correct "
            "source; this is the share of them that were found. *(Recall@5)*\n"
            "- **of 5 shown, share correct** — necessarily low: most questions have "
            "only one or two correct sources, so three of the five slots can never "
            "be right. *(Precision@5)*\n"
            "- **ranking quality** — a single number combining position and "
            "correctness. Rewards putting the right source *first*, not merely "
            "somewhere in the list. *(MRR)*\n"
        ),
        tr=(
            "\n**Sütunlar ne anlama geliyor.** Tüm değerler 0 ile 1 arasında, yüksek "
            "olan iyidir.\n\n"
            "- **doğru kaynak 1. sırada** — ilk sonucun doğru çıkma oranı. En katı "
            "ölçüt ve pratikte en önemlisi: insanlar en üsttekini okur. *(HitRate@1)*\n"
            "- **ilk 5'te bulundu** — doğru kaynağın gösterilen beş sonuçtan herhangi "
            "birinde çıkma oranı. *(HitRate@5)*\n"
            "- **tüm kaynaklar ilk 5'te** — bazı soruların birden fazla doğru kaynağı "
            "var; bunların ne kadarının bulunduğunu gösterir. *(Recall@5)*\n"
            "- **5 sonuçtan doğru oranı** — zorunlu olarak düşük: soruların çoğunun "
            "tek veya iki doğru kaynağı olduğundan, beş sıranın üçü hiçbir zaman "
            "doğru olamaz. *(Precision@5)*\n"
            "- **sıralama kalitesi** — konumu ve doğruluğu birleştiren tek sayı. "
            "Doğru kaynağı listeye sokmayı değil, *başa* koymayı ödüllendirir. "
            "*(MRR)*\n"
        ),
    )

    best_h1 = max(results, key=lambda r: r["hit_rate"][1])
    best_mrr = max(results, key=lambda r: r["mrr"])
    best_h5 = max(results, key=lambda r: r["hit_rate"][5])
    report.add(
        en=(
            f"**Reading the table.** `{best_h1['chunker']}` ranks the correct source "
            f"first most often ({best_h1['hit_rate'][1]:.3f}) and has the best "
            f"ranking quality ({best_mrr['mrr']:.3f}), which is why it is the "
            f"strategy the system ships with. `{best_h5['chunker']}` edges ahead on "
            f"finding a source anywhere in the top five "
            f"({best_h5['hit_rate'][5]:.3f}): when a whole file is a single piece it "
            f"is harder to miss the right document entirely, but harder to rank it "
            f"top. Splitting on headings gives the search a unit that matches how a "
            f"question is usually scoped — one section, one idea.\n"
        ),
        tr=(
            f"**Tablo nasıl okunur.** Doğru kaynağı en sık ilk sıraya koyan "
            f"`{best_h1['chunker']}` ({best_h1['hit_rate'][1]:.3f}); sıralama "
            f"kalitesinde de en iyi o ({best_mrr['mrr']:.3f}). Sistemde kullanılan "
            f"strateji bu. İlk 5'te bulma ölçütünde ise `{best_h5['chunker']}` önde "
            f"({best_h5['hit_rate'][5]:.3f}): dosyanın tamamı tek parça olduğunda "
            f"doğru dokümanı tamamen kaçırmak zorlaşıyor, ama onu ilk sıraya koymak "
            f"da zorlaşıyor. Başlıklardan bölmek, arama sistemine bir sorunun "
            f"kapsamına denk düşen bir birim veriyor: bir bölüm, bir fikir.\n"
        ),
    )

    report.add(
        en="## Does returning more results help?\n",
        tr="## Daha fazla sonuç döndürmek işe yarıyor mu?\n",
    )
    report.add(
        en=(
            "How often a correct source is found, as the number of results shown "
            "grows. A strategy that only catches up at ten results is finding the "
            "right document but burying it.\n"
        ),
        tr=(
            "Gösterilen sonuç sayısı arttıkça doğru kaynağın bulunma oranı. Ancak "
            "on sonuçta başa baş gelen bir strateji, doğru dokümanı buluyor ama "
            "aşağıda bırakıyor demektir.\n"
        ),
    )
    report.add(
        en="| chunker | in 1st | in top 3 | in top 5 | in top 10 |",
        tr="| chunker | 1. sırada | ilk 3'te | ilk 5'te | ilk 10'da |",
    )
    report.both("|---|---|---|---|---|")
    for res in sorted(results, key=lambda r: -r["hit_rate"][1]):
        report.both(
            f"| {res['chunker']} | {best_cell(res['hit_rate'][1], winners['h1'])} | "
            f"{res['hit_rate'][3]:.3f} | {res['hit_rate'][5]:.3f} | {res['hit_rate'][10]:.3f} |"
        )
    report.add(
        en=(
            "\nAll three converge once ten results are shown, so the difference "
            "between them is about ordering, not about which documents they can "
            "reach at all.\n"
        ),
        tr=(
            "\nOn sonuç gösterildiğinde üçü de aynı noktada buluşuyor; yani "
            "aralarındaki fark hangi dokümanlara ulaşabildikleri değil, onları nasıl "
            "sıraladıkları.\n"
        ),
    )

    report.add(
        en="## Rejecting questions the vault does not cover\n",
        tr="## Bilgi tabanının kapsamadığı soruları reddetmek\n",
    )
    report.add(
        en=(
            "A retriever always returns its closest matches, even for a question the "
            "corpus has nothing to say about. This checks whether a simple cutoff on "
            "the bi-encoder's similarity score is enough to catch those.\n"
        ),
        tr=(
            "Arama sistemi, corpus'un hakkında hiçbir şey söylemediği bir soru için "
            "bile en yakın eşleşmeleri döndürür. Buradaki soru şu: bi-encoder'ın "
            "benzerlik skoruna konacak basit bir eşik, bu tür soruları yakalamaya "
            "yeter mi?\n"
        ),
    )
    report.add(
        en="| chunker | out-of-scope | correctly rejected below 0.3 |",
        tr="| chunker | kapsam dışı soru | 0.3 altında doğru reddedilen |",
    )
    report.both("|---|---|---|")
    for name, oos in oos_results:
        report.both(f"| {name} | {oos['n_oos']} | {oos['below_threshold']}/{oos['n_oos']} |")
    report.add(
        en=(
            "\nIt is not: no chunking strategy reliably separates in-scope from "
            "out-of-scope questions on similarity alone. This negative result is what "
            "led to the cross-encoder gate the system now uses. Two other reports "
            "follow it up — *Out-of-scope threshold analysis* shows why the raw "
            "similarity score fails, and *Threshold selection* shows how the "
            "replacement cutoff was fitted.\n"
        ),
        tr=(
            "\nYetmiyor: hiçbir chunking stratejisi, yalnızca benzerlik skoruna "
            "bakarak kapsam içi ve kapsam dışı soruları güvenilir şekilde ayıramıyor. "
            "Sistemde şu an kullanılan cross-encoder tabanlı kapsam denetimi bu "
            "negatif sonucun ardından geldi. Devamı iki raporda: *Kapsam-dışı eşik "
            "analizi* ham benzerlik skorunun neden yetersiz kaldığını, *Eşik seçimi* "
            "ise yerine gelen eşiğin nasıl belirlendiğini anlatıyor.\n"
        ),
    )

    written = report.write(RESULTS_DIR, "chunking")
    print("\nWritten:")
    for path in written:
        print(f"  {path}")


if __name__ == "__main__":
    main()
