"""Threshold calibration analysis for out-of-scope rejection.

Finding: a fixed similarity threshold (0.3) fails to separate in-scope
from out-of-scope questions on the evaluation set. This script examines
(1) the score distribution across the eval set's in-scope and out-of-scope
questions, and (2) how reliable a threshold really is once a broader
out-of-scope sample (technical-other-domain + everyday questions) is
added. Test questions are kept in Turkish, matching the vault's own
language.
"""

import sys
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from config import CACHE_DIR, INDEX_DIR, RESULTS_DIR
from embedder import Embedder
from report import Report
from store import load_index

# A broader out-of-scope sample than what's in the formal eval set. Two
# subgroups: "technical, different domain" (other software/engineering
# fields) and "everyday" (no technical overlap with the vault at all).
EXTRA_OOS_TECHNICAL = [
    "Transformer mimarisinde self-attention nasıl çalışır?",
    "Kubernetes pod network policy nasıl tanımlanır?",
    "React useEffect hook ne zaman tetiklenir?",
    "Blockchain konsensüs algoritmaları nelerdir?",
]
EXTRA_OOS_EVERYDAY = [
    "En sevdiğim yemek tarifi hangisi?",
    "İstanbulda hava durumu nasıl?",
    "Kedi bakımı için neler gerekli?",
    "Dünyanın en yüksek dağı hangisi?",
    "Osmanlı İmparatorluğu ne zaman kuruldu?",
    "Bitcoin fiyatı bugün ne kadar?",
]


def top1_scores(questions: list[str], embedder: Embedder, embeddings: np.ndarray) -> list[float]:
    scores = []
    for q in questions:
        qvec = embedder.embed([q])[0]
        scores.append(float(np.max(embeddings @ qvec)))
    return scores


def main():
    questions_path = Path(__file__).parent.parent / "eval" / "questions.yaml"
    with open(questions_path, encoding="utf-8") as f:
        questions = yaml.safe_load(f)["questions"]

    embedder = Embedder(CACHE_DIR)
    chunks, embeddings = load_index(INDEX_DIR, "whole_doc")

    in_scope_qs = [q["question"] for q in questions if q["expected"]]
    eval_oos_qs = [q["question"] for q in questions if not q["expected"]]

    in_scope_scores = top1_scores(in_scope_qs, embedder, embeddings)
    eval_oos_scores = top1_scores(eval_oos_qs, embedder, embeddings)
    tech_oos_scores = top1_scores(EXTRA_OOS_TECHNICAL, embedder, embeddings)
    everyday_oos_scores = top1_scores(EXTRA_OOS_EVERYDAY, embedder, embeddings)

    all_oos_scores = eval_oos_scores + tech_oos_scores + everyday_oos_scores

    report = Report()
    report.add(
        en="# Why Wasn't a Simple Cutoff Enough?\n",
        tr="# Basit Bir Eşik Neden Yetmedi?\n",
    )
    report.add(
        en=(
            "The search always returns something. Ask it about a topic the notes never "
            "cover and it still hands back its five closest guesses, with no sign that "
            "they are unrelated.\n\n"
            "The obvious fix is a cutoff: every result carries a similarity score "
            "between 0 and 1, so refuse to answer when the best score is too low. This "
            "report tests whether any such cutoff actually works.\n"
        ),
        tr=(
            "Arama her zaman bir şey döndürür. Notlarda hiç geçmeyen bir konuyu "
            "sorduğunuzda bile en yakın beş tahminini verir ve bunların alakasız "
            "olduğuna dair hiçbir işaret göstermez.\n\n"
            "Akla gelen ilk çözüm bir eşik koymak: her sonucun 0 ile 1 arasında bir "
            "benzerlik skoru var, en iyi skor çok düşükse cevap vermeyi reddet. Bu "
            "rapor, böyle bir eşiğin gerçekten işe yarayıp yaramadığını test ediyor.\n"
        ),
    )

    report.add(
        en="## How the scores are distributed\n",
        tr="## Skorlar nasıl dağılıyor\n",
    )
    report.add(
        en=(
            "Three kinds of question, and the similarity score each one's best match "
            "received. If a cutoff is going to work, these groups have to separate.\n"
        ),
        tr=(
            "Üç tür soru ve her birinin en iyi eşleşmesinin aldığı benzerlik skoru. "
            "Bir eşiğin işe yaraması için bu grupların birbirinden ayrılması gerekir.\n"
        ),
    )
    report.add(
        en="| question type | count | lowest | highest | average |",
        tr="| soru türü | adet | en düşük | en yüksek | ortalama |",
    )
    report.both("|---|---|---|---|---|")
    groups = [
        (
            "covered by the notes",
            "notlarda işlenen konular",
            in_scope_scores,
        ),
        (
            "out of scope, from the question set",
            "kapsam dışı, test setinden",
            eval_oos_scores,
        ),
        (
            "out of scope, other technical fields",
            "kapsam dışı, başka teknik alanlar",
            tech_oos_scores,
        ),
        (
            "out of scope, everyday topics",
            "kapsam dışı, günlük konular",
            everyday_oos_scores,
        ),
    ]
    for en_label, tr_label, scores in groups:
        row = f"| {{label}} | {len(scores)} | {min(scores):.3f} | {max(scores):.3f} | {np.mean(scores):.3f} |"
        report.add(en=row.format(label=en_label), tr=row.format(label=tr_label))

    report.add(
        en=(
            "\nThe ranges overlap. Questions the notes do cover go as low as "
            f"{min(in_scope_scores):.3f}, while unrelated technical questions reach "
            f"{max(tech_oos_scores):.3f} — so there is no line that cleanly separates "
            "them.\n"
        ),
        tr=(
            "\nAralıklar üst üste biniyor. Notlarda işlenen sorular "
            f"{min(in_scope_scores):.3f} kadar aşağı inebiliyor, alakasız teknik "
            f"sorular ise {max(tech_oos_scores):.3f} kadar yukarı çıkabiliyor — yani "
            "ikisini temiz şekilde ayıran bir çizgi yok.\n"
        ),
    )

    report.add(en="## Every cutoff, and what it costs\n", tr="## Her eşik ve maliyeti\n")
    report.add(
        en=(
            "Two kinds of mistake pull in opposite directions: a strict cutoff turns "
            "away real questions, a loose one lets unrelated ones through.\n"
        ),
        tr=(
            "İki hata türü birbirinin tersi yönde çekiyor: katı bir eşik gerçek "
            "soruları geri çeviriyor, gevşek bir eşik alakasızları içeri alıyor.\n"
        ),
    )
    report.add(
        en="| cutoff | real questions wrongly refused | unrelated questions wrongly accepted |",
        tr="| eşik | yanlışlıkla reddedilen gerçek soru | yanlışlıkla kabul edilen alakasız soru |",
    )
    report.both("|---|---|---|")
    for t in [0.30, 0.35, 0.38, 0.40, 0.42, 0.45, 0.50]:
        fn = sum(1 for s in in_scope_scores if s < t)
        fp = sum(1 for s in all_oos_scores if s >= t)
        report.both(f"| {t:.2f} | {fn}/{len(in_scope_scores)} | {fp}/{len(all_oos_scores)} |")

    report.add(en="## What this means\n", tr="## Bu ne anlama geliyor\n")
    report.add(
        en=(
            "**Everyday questions are easy to catch.** Weather, cooking, history — "
            "they share no vocabulary with the notes at all, so they score low and a "
            "cutoff turns them away reliably.\n\n"
            "**Questions from other technical fields are not.** Kubernetes, React, "
            "Blockchain — these score in the same range as genuine questions, because "
            "they are written in the same register: technical prose, similar sentence "
            "shapes, overlapping words like \"model\", \"sistem\", \"veri\". One "
            "question about a food recipe even matched the recommendation-systems "
            "pages, because *tarif* and *öneri* sit close together in the model's view "
            "of meaning.\n\n"
            "**So no single cutoff works.** Tightening it to shut out the technical "
            "questions starts refusing real ones; loosening it to let real ones "
            "through lets the technical ones in. Catching the hard cases needs a "
            "different signal, not a better number on the same one — which is what "
            "the report on *how the threshold was chosen* goes on to build.\n"
        ),
        tr=(
            "**Günlük soruları yakalamak kolay.** Hava durumu, yemek, tarih — bunlar "
            "notlarla hiçbir kelime paylaşmıyor, düşük skor alıyorlar ve bir eşik "
            "onları güvenilir şekilde geri çeviriyor.\n\n"
            "**Başka teknik alanların soruları değil.** Kubernetes, React, Blockchain — "
            "bunlar gerçek sorularla aynı aralıkta skor alıyor, çünkü aynı üslupla "
            "yazılmışlar: teknik anlatım, benzer cümle yapıları, \"model\", \"sistem\", "
            "\"veri\" gibi örtüşen kelimeler. Bir yemek tarifi sorusu bile öneri "
            "sistemleri sayfalarıyla eşleşti, çünkü *tarif* ve *öneri* modelin anlam "
            "haritasında birbirine yakın duruyor.\n\n"
            "**Yani tek bir eşik yetmiyor.** Teknik soruları dışarıda bırakacak kadar "
            "sıkarsanız gerçek soruları reddetmeye başlıyor; gerçek soruları içeri "
            "alacak kadar gevşetirseniz teknik olanlar da giriyor. Zor vakaları "
            "yakalamak için aynı sinyalin daha iyi bir sayısı değil, farklı bir sinyal "
            "gerekiyor — *eşik nasıl belirlendi* raporu bunu kuruyor.\n"
        ),
    )

    written = report.write(RESULTS_DIR, "threshold_analysis")
    print("\nWritten:")
    for p in written:
        print(f"  {p}")


if __name__ == "__main__":
    main()
