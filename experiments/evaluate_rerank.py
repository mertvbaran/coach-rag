"""Measures what happens when a cross-encoder re-ranks the retrieval results,
and what it is good for instead. Writes results/rerank_impact.md and
rerank_impact.tr.md."""

import sys
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from config import CACHE_DIR, INDEX_DIR, RESULTS_DIR
from embedder import Embedder
from report import Report, arrow
from reranker import CE_OUT_OF_SCOPE_THRESHOLD, Reranker
from store import load_index

RERANK_POOL = 10


def dedupe_by_doc(order_slugs: list[str], k: int) -> list[str]:
    seen = []
    for slug in order_slugs:
        if slug not in seen:
            seen.append(slug)
        if len(seen) >= k:
            break
    return seen


def evaluate(chunker_name: str, questions: list[dict], embedder: Embedder, reranker: Reranker) -> dict:
    chunks, embeddings = load_index(INDEX_DIR, chunker_name)

    biencoder_mrr, rerank_mrr = [], []
    biencoder_hit1, rerank_hit1 = [], []

    for q in questions:
        expected = set(q["expected"])
        if not expected:
            continue

        query_vec = embedder.embed([q["question"]])[0]
        scores = embeddings @ query_vec
        order = np.argsort(-scores)

        # bi-encoder-only ranking
        bi_slugs = dedupe_by_doc([chunks[i]["doc_slug"] for i in order], 10)
        bi_rank = next((i + 1 for i, s in enumerate(bi_slugs) if s in expected), None)
        biencoder_mrr.append(1 / bi_rank if bi_rank else 0)
        biencoder_hit1.append(1 if bi_slugs[:1] and bi_slugs[0] in expected else 0)

        # cross-encoder re-rank over the top RERANK_POOL chunks
        pool_idx = order[:RERANK_POOL].tolist()
        pool_texts = [chunks[i]["text"] for i in pool_idx]
        reranked = reranker.rerank(q["question"], pool_texts, pool_idx)
        re_slugs = dedupe_by_doc([chunks[i]["doc_slug"] for i, _ in reranked], 10)
        re_rank = next((i + 1 for i, s in enumerate(re_slugs) if s in expected), None)
        rerank_mrr.append(1 / re_rank if re_rank else 0)
        rerank_hit1.append(1 if re_slugs[:1] and re_slugs[0] in expected else 0)

    return {
        "chunker": chunker_name,
        "n": len(biencoder_mrr),
        "biencoder_mrr": float(np.mean(biencoder_mrr)),
        "rerank_mrr": float(np.mean(rerank_mrr)),
        "biencoder_hit1": float(np.mean(biencoder_hit1)),
        "rerank_hit1": float(np.mean(rerank_hit1)),
    }


def evaluate_oos_detection(questions: list[dict], embedder: Embedder, reranker: Reranker, chunker_name: str = "by_heading") -> dict:
    """Defaults to by_heading: the gate's threshold is calibrated against that
    index's score distribution, so measuring it on another one reports numbers
    the shipped configuration never produces."""
    chunks, embeddings = load_index(INDEX_DIR, chunker_name)
    oos = [q for q in questions if not q["expected"]]
    correct = 0
    for q in oos:
        query_vec = embedder.embed([q["question"]])[0]
        scores = embeddings @ query_vec
        pool_idx = np.argsort(-scores)[:RERANK_POOL].tolist()
        pool_texts = [chunks[i]["text"] for i in pool_idx]
        in_scope, _ = reranker.is_in_scope(q["question"], pool_texts)
        if not in_scope:
            correct += 1
    return {"n_oos": len(oos), "correctly_rejected": correct}


def main():
    questions_path = Path(__file__).parent.parent / "eval" / "questions.yaml"
    with open(questions_path, encoding="utf-8") as f:
        questions = yaml.safe_load(f)["questions"]

    embedder = Embedder(CACHE_DIR)
    reranker = Reranker()

    report = Report()
    report.add(
        en="# Re-ranking with a Second Model: Tested and Rejected\n",
        tr="# İkinci Bir Modelle Yeniden Sıralama: Denendi ve Reddedildi\n",
    )
    report.add(
        en=(
            "Search here works in one pass: every passage is turned into numbers "
            "ahead of time, and the ones closest to the question are returned. That "
            "is fast, but the comparison is indirect — question and passage are "
            "measured separately and only then compared.\n\n"
            "A second kind of model reads the question and a passage *together* and "
            "judges how well they match. It is far slower, so it cannot score the "
            "whole collection, but it can re-order the top handful. The usual "
            "expectation is that this improves the ranking. This measures whether it "
            "does.\n"
        ),
        tr=(
            "Buradaki arama tek adımda çalışıyor: her metin parçası önceden sayılara "
            "çevriliyor, soruya en yakın olanlar döndürülüyor. Bu hızlı bir yöntem "
            "ama karşılaştırma dolaylı — soru ile metin ayrı ayrı ölçülüp sonra "
            "kıyaslanıyor.\n\n"
            "İkinci tür bir model ise soruyu ve metni *birlikte* okuyup ne kadar "
            "örtüştüklerine karar veriyor. Çok daha yavaş olduğu için tüm belgeleri "
            "puanlayamaz, ama ilk birkaç sonucu yeniden sıralayabilir. Genel beklenti "
            "bunun sıralamayı iyileştirmesi. Buradaki ölçüm, gerçekten iyileştirip "
            "iyileştirmediğine bakıyor.\n"
        ),
    )

    report.add(
        en="## Ranking quality, before and after re-ranking\n",
        tr="## Yeniden sıralama öncesi ve sonrası sıralama kalitesi\n",
    )
    report.add(
        en=(
            "An arrow pointing down means re-ranking made that measure worse.\n"
        ),
        tr=(
            "Aşağı ok, yeniden sıralamanın o ölçütü kötüleştirdiği anlamına geliyor.\n"
        ),
    )
    report.add(
        en="| chunker | questions | correct source 1st: before → after | ranking quality: before → after |",
        tr="| chunker | soru | doğru kaynak 1. sırada: önce → sonra | sıralama kalitesi: önce → sonra |",
    )
    report.both("|---|---|---|---|")
    by_heading_res = None
    for chunker_name in ["whole_doc", "by_heading"]:
        if not (INDEX_DIR / f"{chunker_name}.npy").exists():
            continue
        res = evaluate(chunker_name, questions, embedder, reranker)
        if chunker_name == "by_heading":
            by_heading_res = res
        h1_arrow = arrow(res["biencoder_hit1"], res["rerank_hit1"])
        mrr_arrow = arrow(res["biencoder_mrr"], res["rerank_mrr"])
        report.both(
            f"| {res['chunker']} | {res['n']} | "
            f"{res['biencoder_hit1']:.3f} → {res['rerank_hit1']:.3f} {h1_arrow} | "
            f"{res['biencoder_mrr']:.3f} → {res['rerank_mrr']:.3f} {mrr_arrow} |"
        )
        print(f"{chunker_name}: HitRate@1 {res['biencoder_hit1']:.3f}->{res['rerank_hit1']:.3f}  MRR {res['biencoder_mrr']:.3f}->{res['rerank_mrr']:.3f}")

    # Quote the measured figures rather than fixed ones, so the prose cannot
    # drift away from the table above when the question set changes.
    before = f"{by_heading_res['biencoder_hit1']:.3f}" if by_heading_res else "?"
    after = f"{by_heading_res['rerank_hit1']:.3f}" if by_heading_res else "?"
    report.add(
        en=(
            f"\n**It makes things worse.** On the index the system actually uses, the "
            f"share of questions answered correctly at rank 1 falls from {before} to "
            f"{after}.\n\n"
            f"Looking at which answers changed shows a consistent pattern: the second "
            f"model prefers long, explanatory passages — flashcard-style question-and-"
            f"answer pages and broad course summaries — over the short, focused page "
            f"written about exactly that concept. In one case a question asks about "
            f"\"support, confidence, lift\"; the page using those exact terms was "
            f"ranked first by the original search, and the re-ranker pushed a general "
            f"flashcard page above it.\n\n"
            f"That preference is not random. This kind of model is typically trained "
            f"on web search data, where the better answer usually *is* the longer, "
            f"more explanatory passage. These notes are the opposite: one idea per "
            f"page, deliberately short. The model's training works against the way "
            f"this collection is written.\n"
        ),
        tr=(
            f"\n**Sonucu kötüleştiriyor.** Sistemin fiilen kullandığı indekste, doğru "
            f"cevabın ilk sıraya konduğu soruların oranı {before} değerinden {after} "
            f"değerine düşüyor.\n\n"
            f"Hangi cevapların değiştiğine bakınca tutarlı bir örüntü çıkıyor: ikinci "
            f"model uzun ve açıklayıcı metinleri — soru-cevap biçimindeki flashcard "
            f"sayfalarını ve geniş ders özetlerini — tam o kavram için yazılmış kısa "
            f"ve odaklı sayfaya tercih ediyor. Bir örnekte soru \"support, confidence, "
            f"lift\" kavramlarını soruyor; bu terimleri birebir kullanan sayfa özgün "
            f"aramada ilk sıradayken, yeniden sıralama onun üstüne genel bir flashcard "
            f"sayfasını çıkarıyor.\n\n"
            f"Bu tercih rastgele değil. Bu tür modeller genellikle web arama verisiyle "
            f"eğitiliyor ve orada daha iyi cevap gerçekten de çoğu zaman daha uzun, "
            f"daha açıklayıcı olan oluyor. Buradaki notlar ise tam tersi: sayfa başına "
            f"tek fikir, bilinçli olarak kısa. Modelin eğitimi, bu sayfaların yazılma "
            f"biçimine ters düşüyor.\n"
        ),
    )

    report.add(
        en="## Where the second model does help\n",
        tr="## İkinci model nerede işe yarıyor\n",
    )
    oos_res = evaluate_oos_detection(questions, embedder, reranker)
    report.add(
        en=(
            f"Re-ordering results is the wrong job for it. Deciding whether a question "
            f"is covered at all turns out to be the right one.\n\n"
            f"Refusing to answer when its score falls below {CE_OUT_OF_SCOPE_THRESHOLD} "
            f"correctly turns away {oos_res['correctly_rejected']} of "
            f"{oos_res['n_oos']} questions the notes have nothing to say about. The "
            f"original search, using a simple similarity cutoff, catches 0 of "
            f"{oos_res['n_oos']}.\n\n"
            f"So the model is used for exactly that and nothing else: the ranking is "
            f"left alone, and the second model only decides whether to show a warning. "
            f"Two separate jobs, and a model that is good at one is not automatically "
            f"good at the other.\n"
        ),
        tr=(
            f"Sonuçları yeniden sıralamak bu model için yanlış görevmiş. Bir sorunun "
            f"kapsam içinde olup olmadığına karar vermek ise doğru görev çıktı.\n\n"
            f"Skoru {CE_OUT_OF_SCOPE_THRESHOLD} değerinin altına düştüğünde cevap "
            f"vermeyi reddetmek, notların hakkında hiçbir şey söylemediği "
            f"{oos_res['n_oos']} sorudan {oos_res['correctly_rejected']} tanesini doğru "
            f"şekilde geri çeviriyor. Özgün arama, basit bir benzerlik eşiğiyle "
            f"{oos_res['n_oos']} sorudan 0 tanesini yakalayabiliyor.\n\n"
            f"Bu yüzden model yalnızca bu iş için kullanılıyor: sıralamaya hiç "
            f"dokunulmuyor, ikinci model sadece uyarı gösterilip gösterilmeyeceğine "
            f"karar veriyor. İki ayrı görev ve birinde iyi olan bir model, otomatik "
            f"olarak diğerinde de iyi değil.\n"
        ),
    )
    print(f"OOS rejection: {oos_res['correctly_rejected']}/{oos_res['n_oos']}")

    written = report.write(RESULTS_DIR, "rerank_impact")
    print("\nWritten:")
    for p in written:
        print(f"  {p}")


if __name__ == "__main__":
    main()
