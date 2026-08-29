"""Tests how sensitive the cross-encoder out-of-scope threshold (see
reranker.py) is to paraphrasing the same question.

Found interactively: "Kubernetes pod network policy nasil tanimlanir?"
(the calibration sample's exact wording) scores below threshold, but
"Kubernetes'te pod'lar arasi network policy nasil tanimlanir?" (a more
natural phrasing of the same question) scored -5.46 against the threshold
in force at the time (-5.5) -- just 0.04 above it, flipping the gate's
decision. This checks whether that was a one-off or a systematic weakness
across several out-of-scope questions and their paraphrases.

Writes results/threshold_robustness.md and .tr.md.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import CACHE_DIR, INDEX_DIR, RESULTS_DIR
from embedder import Embedder
from report import Report
from reranker import CE_OUT_OF_SCOPE_THRESHOLD, Reranker
from store import load_index, search

RERANK_POOL_SIZE = 10

# Each entry: a genuinely out-of-scope topic, with the calibration-set
# wording plus 2-3 natural paraphrases of the same question.
PARAPHRASE_GROUPS = {
    "Kubernetes network policy": [
        "Kubernetes pod network policy nasıl tanımlanır?",
        "Kubernetes'te pod'lar arası network policy nasıl tanımlanır?",
        "Kubernetes'te pod'lar arasındaki ağ trafiğini nasıl kısıtlarım?",
    ],
    "React useEffect": [
        "React useEffect hook ne zaman tetiklenir?",
        "React'te useEffect hook'u ne zaman çalışır?",
        "useEffect'in bağımlılık dizisi (dependency array) nasıl çalışır?",
    ],
    "Blockchain consensus": [
        "Blockchain konsensüs algoritmaları nelerdir?",
        "Blockchain'de konsensüs nasıl sağlanır?",
        "Proof of work ile proof of stake arasındaki fark nedir?",
    ],
    "Transformer attention": [
        "Transformer mimarisinde self-attention nasıl çalışır?",
        "Transformer'larda self-attention mekanizması nedir?",
        "Attention is all you need makalesindeki temel fikir nedir?",
    ],
}


def main():
    chunks, embeddings = load_index(INDEX_DIR, "by_heading")
    embedder = Embedder(CACHE_DIR)
    reranker = Reranker()

    report = Report()
    report.add(
        en="# Is the Threshold Robust to Rephrasing?\n",
        tr="# Eşik Farklı İfadelere Dayanıklı mı?\n",
    )
    report.add(
        en=(
            f"The out-of-scope gate (threshold {CE_OUT_OF_SCOPE_THRESHOLD}, see "
            f"threshold_selection.md for how it was fitted) was checked against "
            f"one fixed wording per out-of-scope topic during calibration. This "
            f"asks a different question: does rephrasing the same question -- "
            f"same topic, same intent, different words -- change the gate's "
            f"decision?\n"
        ),
        tr=(
            f"Kapsam-dışı denetimi (eşik {CE_OUT_OF_SCOPE_THRESHOLD}, nasıl "
            f"hesaplandığı için bkz. threshold_selection.md) kalibrasyon "
            f"sırasında kapsam dışı her konu için tek bir sabit ifadeyle "
            f"sınanmıştı. Burada farklı bir soru soruluyor: aynı soru farklı "
            f"kelimelerle sorulduğunda -- aynı konu, aynı niyet, farklı "
            f"kelimeler -- denetimin kararı değişiyor mu?\n"
        ),
    )

    any_flip = False
    for topic, questions in PARAPHRASE_GROUPS.items():
        report.add(en=f"## {topic}\n", tr=f"## {topic}\n")
        report.add(
            en="| question | CE score | in scope? |",
            tr="| soru | CE skoru | kapsamda mı? |",
        )
        report.both("|---|---|---|")
        scores = []
        for q in questions:
            query_vec = embedder.embed([q])[0]
            pool = search(query_vec, embeddings, k=RERANK_POOL_SIZE)
            pool_texts = [chunks[idx]["text"] for idx, _ in pool]
            in_scope, ce_score = reranker.is_in_scope(q, pool_texts)
            scores.append(ce_score)
            if in_scope:
                any_flip = True
                flag_en, flag_tr = "**wrongly accepted**", "**yanlışlıkla kabul edildi**"
            else:
                flag_en, flag_tr = "correctly rejected", "doğru şekilde reddedildi"
            report.add(
                en=f"| {q} | {ce_score:.2f} | {flag_en} |",
                tr=f"| {q} | {ce_score:.2f} | {flag_tr} |",
            )
        spread = max(scores) - min(scores)
        report.add(
            en=f"\nSpread across paraphrases: {spread:.2f} (scores range {min(scores):.2f} to {max(scores):.2f})\n",
            tr=f"\nİfadeler arası fark: {spread:.2f} (skorlar {min(scores):.2f} ile {max(scores):.2f} arasında)\n",
        )

    report.add(en="## Interpretation\n", tr="## Yorum\n")
    if any_flip:
        report.add(
            en=(
                "At least one paraphrase of a genuinely out-of-scope question "
                "was wrongly accepted by the gate. Real usage paraphrases "
                "questions naturally, and this shows the current cutoff sits "
                "close enough to some topics' natural score range that minor "
                "rewording can cross it. This is a real limitation of a single "
                "fixed threshold on a single cross-encoder score, not a bug in "
                "the calibration -- the fix would need either a wider safety "
                "margin (fewer false accepts, more false refusals on legitimate "
                "borderline in-scope questions) or a second signal alongside the "
                "cross-encoder score (e.g. agreement across the top-k retrieved "
                "chunks), not a single number.\n"
            ),
            tr=(
                "Kapsam dışı bir konunun en az bir ifade biçimi, denetim "
                "tarafından yanlışlıkla kabul edildi. Gerçek kullanımda sorular "
                "doğal olarak farklı ifadelerle sorulur, ve bu durum güncel "
                "eşiğin bazı konuların doğal skor aralığına yeterince yakın "
                "olduğunu, küçük bir ifade değişikliğinin bile bu sınırı "
                "aşabildiğini gösteriyor. Bu, kalibrasyondaki bir hata değil, "
                "tek bir cross-encoder skoruna dayanan tek bir sabit eşiğin "
                "gerçek bir sınırlılığı -- düzeltme ya daha geniş bir güvenlik "
                "payı (daha az yanlış kabul, sınırda kalan meşru sorularda daha "
                "fazla yanlış red) ya da cross-encoder skorunun yanına ikinci "
                "bir sinyal (örn. ilk k getirilen parça arasındaki uyum) "
                "gerektirir, tek bir sayı değil.\n"
            ),
        )
    else:
        report.add(
            en=(
                "All paraphrases were correctly rejected in this sample -- the "
                "threshold held up across rewordings here, though the earlier "
                "interactive finding (Kubernetes phrasing scoring -5.46 against "
                "the threshold then in force) shows it is not universally "
                "robust.\n"
            ),
            tr=(
                "Bu örnekteki tüm ifadeler doğru şekilde reddedildi -- eşik "
                "burada farklı ifadelere karşı dayanıklı çıktı, ama daha önceki "
                "canlı kullanım bulgusu (Kubernetes ifadesinin o zamanki eşiğe "
                "karşı -5.46 alması) eşiğin evrensel olarak dayanıklı "
                "olmadığını gösteriyor.\n"
            ),
        )

    written = report.write(RESULTS_DIR, "threshold_robustness")
    print("Written:")
    for p in written:
        print(f"  {p}")


if __name__ == "__main__":
    main()
