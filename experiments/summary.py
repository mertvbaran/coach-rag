"""Writes the overview page shown first in the dashboard's results tab.

Everything here is read back from the reports the other scripts produced, so
the summary cannot quietly drift out of step with them. Run it last.

Writes results/summary.md and summary.tr.md.
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import yaml

from config import INDEX_DIR, RESULTS_DIR
from report import Report
from reranker import CE_OUT_OF_SCOPE_THRESHOLD
from store import load_index


def read_table_numbers(path: Path, row_label: str) -> list[str]:
    """Pulls the cells out of the first markdown table row starting with a label.

    Reading the figures back out of the generated reports keeps this page
    honest: if a measurement changes, the summary changes with it.
    """
    if not path.exists():
        return []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("|") and row_label in line:
            cells = [c.strip() for c in line.strip("|").split("|")]
            return [re.sub(r"[*↑↓→\s]", "", c) for c in cells]
    return []


def main():
    questions = yaml.safe_load(
        (Path(__file__).parent.parent / "eval" / "questions.yaml").read_text(encoding="utf-8")
    )["questions"]
    n_questions = len(questions)
    n_scored = sum(1 for q in questions if q["expected"])
    n_oos = sum(1 for q in questions if not q["expected"])

    chunks, _ = load_index(INDEX_DIR, "by_heading")
    n_chunks = len(chunks)
    n_docs = len({c["doc_slug"] for c in chunks})

    chunking = read_table_numbers(RESULTS_DIR / "chunking.md", "by_heading")
    hit1 = chunking[2] if len(chunking) > 2 else "?"
    baseline = read_table_numbers(RESULTS_DIR / "chunking.md", "fixed_window")
    hit1_baseline = baseline[2] if len(baseline) > 2 else "?"

    gate = read_table_numbers(RESULTS_DIR / "abstention_metrics.md", "all together")
    separation = gate[2] if len(gate) > 2 else "?"

    report = Report()
    report.add(en="# Overview\n", tr="# Genel Bakış\n")
    report.add(
        en=(
            "A search tool over a personal knowledge base. Ask a question in plain "
            "language, get back the passages that answer it, each with its source. "
            "Everything runs on the machine it is installed on — no text is sent "
            "anywhere.\n"
        ),
        tr=(
            "Kişisel bir bilgi tabanı üzerinde çalışan bir arama aracı. Gündelik dille "
            "bir soru sorup cevabı içeren bölümleri kaynağıyla birlikte alıyorsunuz. "
            "Her şey kurulu olduğu makinede çalışıyor — hiçbir metin dışarı "
            "gönderilmiyor.\n"
        ),
    )

    report.add(en="## How it works\n", tr="## Nasıl çalışıyor\n")
    report.add(
        en=(
            f"Ordinary search matches words. This matches meaning: every passage in "
            f"the notes is converted into a list of numbers that stands for what it "
            f"says, the question is converted the same way, and the closest passages "
            f"come back. A question phrased differently from the notes still finds "
            f"them.\n\n"
            f"The collection is {n_docs} files, cut into {n_chunks} passages at their "
            f"section headings.\n"
        ),
        tr=(
            f"Sıradan arama kelimeleri eşleştirir. Bu ise anlamı eşleştiriyor: "
            f"notlardaki her metin parçası, ne anlattığını temsil eden bir sayı "
            f"dizisine çevriliyor; soru da aynı şekilde çevriliyor ve en yakın "
            f"parçalar geri geliyor. Notlardan farklı kelimelerle sorulmuş bir soru "
            f"bile onları bulabiliyor.\n\n"
            f"Koleksiyon {n_docs} dosyadan oluşuyor ve bölüm başlıklarından "
            f"{n_chunks} parçaya ayrılmış durumda.\n"
        ),
    )

    report.add(en="## How well it works\n", tr="## Ne kadar iyi çalışıyor\n")
    report.add(
        en=(
            f"Measured on {n_questions} questions written against the notes: "
            f"{n_scored} with a known correct source, {n_oos} deliberately about "
            f"topics the notes never cover.\n"
        ),
        tr=(
            f"İçeriğe göre yazılmış {n_questions} soru üzerinde ölçüldü: {n_scored} "
            f"tanesinin doğru kaynağı biliniyor, {n_oos} tanesi ise bilerek bilgi "
            f"tabanında hiç geçmeyen konularda.\n"
        ),
    )
    report.add(
        en="| | result |",
        tr="| | sonuç |",
    )
    report.both("|---|---|")
    def as_percent(value: str, lang: str = "en") -> str:
        """0.809 -> '81%' or '%81'. Turkish puts the sign before the number."""
        try:
            n = f"{float(value) * 100:.0f}"
        except ValueError:
            return value
        return f"%{n}" if lang == "tr" else f"{n}%"

    report.add(
        en=f"| correct source ranked first | **{as_percent(hit1)}** of questions |",
        tr=f"| doğru kaynak ilk sırada | soruların **{as_percent(hit1, 'tr')}**'i |",
    )
    report.add(
        en=f"| same, without using document structure | {as_percent(hit1_baseline)} |",
        tr=f"| aynısı, belge yapısı kullanılmadan | {as_percent(hit1_baseline, 'tr')} |",
    )
    report.add(
        en=f"| telling covered from uncovered questions apart | **{separation}** out of 1.0 |",
        tr=f"| kapsanan ve kapsanmayan soruları ayırt etme | 1.0 üzerinden **{separation}** |",
    )

    report.add(
        en=(
            "\nSplitting documents at their headings rather than by word count is "
            "what accounts for most of the difference between the first two rows — "
            "the same notes, cut differently.\n"
        ),
        tr=(
            "\nİlk iki satır arasındaki farkın büyük kısmı, belgeleri kelime sayısına "
            "göre değil başlıklarına göre bölmekten geliyor — aynı notlar, farklı "
            "kesilmiş.\n"
        ),
    )

    report.add(en="## Knowing when not to answer\n", tr="## Ne zaman cevap vermeyeceğini bilmek\n")
    report.add(
        en=(
            f"A search will always return its closest match, even for a question the "
            f"notes have nothing to do with. So before answering, the system checks "
            f"whether the question is covered at all, and says so when it is not.\n\n"
            f"Getting that check right took three attempts. A simple similarity "
            f"cutoff did not work — questions from other technical fields score just "
            f"as high as real ones. A second model that reads the question and passage "
            f"together did work, but only for this decision: using it to re-order "
            f"results made them worse. And the cutoff itself, first picked by eye, "
            f"turned out to flip its decision when a question was reworded; it is now "
            f"fitted from data at {CE_OUT_OF_SCOPE_THRESHOLD} and checked against "
            f"questions it was not fitted on.\n"
        ),
        tr=(
            f"Arama her zaman en yakın eşleşmesini döndürür — bilgi tabanıyla hiç ilgisi "
            f"olmayan bir soru için bile. Bu yüzden sistem cevap vermeden önce sorunun "
            f"kapsanıp kapsanmadığını denetliyor ve kapsanmıyorsa bunu söylüyor.\n\n"
            f"Bu denetimi doğru kurmak üç deneme aldı. Basit bir benzerlik eşiği işe "
            f"yaramadı — başka teknik alanlardan gelen sorular gerçek sorular kadar "
            f"yüksek skor alıyor. Soruyu ve metni birlikte okuyan ikinci bir model işe "
            f"yaradı, ama yalnızca bu karar için: sonuçları yeniden sıralamak için "
            f"kullanmak onları kötüleştirdi. Eşiğin kendisi ise önce gözle seçilmişti "
            f"ve soru farklı kelimelerle sorulduğunda kararını değiştirdiği ortaya "
            f"çıktı; şimdi veriden hesaplanıyor ({CE_OUT_OF_SCOPE_THRESHOLD}) ve "
            f"hesaplanmadığı sorularla sınanıyor.\n"
        ),
    )

    report.add(en="## What did not work\n", tr="## İşe yaramayanlar\n")
    report.add(
        en=(
            "Three ideas were tried, measured, and dropped. They are kept in the "
            "reports because a measured failure is worth more than an untested "
            "assumption.\n\n"
            "- **Combining meaning-based and keyword search.** Standard advice, but it "
            "made results worse at every mix tested. These notes all share the same "
            "vocabulary, so keyword matching separates almost nothing.\n"
            "- **Re-ordering results with a second model.** Dropped rank-1 accuracy "
            "sharply. That model prefers long, explanatory passages, while these notes "
            "are deliberately short and focused.\n"
            "- **Tuning a rule until it scored perfectly.** It did — on the very "
            "questions used to tune it, then failed on questions held back. A reminder "
            "of why the honest number is the one measured on data the choice was not "
            "made from.\n"
        ),
        tr=(
            "Üç fikir denendi, ölçüldü ve bırakıldı. Raporlarda tutuluyorlar, çünkü "
            "ölçülmüş bir başarısızlık, sınanmamış bir varsayımdan daha değerli.\n\n"
            "- **Anlama dayalı aramayla anahtar kelime aramasını birleştirmek.** Yaygın "
            "bir tavsiye ama denenen her karışım oranında sonuçları kötüleştirdi. Bu "
            "notların hepsi aynı kelime dağarcığını paylaştığından, kelime eşleşmesi "
            "neredeyse hiçbir şeyi ayırt etmiyor.\n"
            "- **Sonuçları ikinci bir modelle yeniden sıralamak.** İlk sıra doğruluğunu "
            "belirgin şekilde düşürdü. O model uzun ve açıklayıcı metinleri tercih "
            "ediyor, bu notlar ise bilinçli olarak kısa ve odaklı.\n"
            "- **Bir kuralı mükemmel skor verene kadar ayarlamak.** Verdi — ama "
            "yalnızca ayarlandığı sorularda; saklanan sorularda başarısız oldu. Dürüst "
            "sayının, seçimin yapılmadığı veride ölçülen sayı olduğunun hatırlatıcısı.\n"
        ),
    )

    report.add(en="## Where to look next\n", tr="## Nereye bakmalı\n")
    report.add(
        en=(
            "The other reports on this tab go into each of these:\n\n"
            "- **How should text be split?** — the comparison behind the numbers above.\n"
            "- **Where the search gets it wrong** — the questions it ranks worst, and "
            "the two patterns behind them.\n"
            "- **Hybrid search** and **Re-ranking** — the two rejected ideas, with "
            "their measurements.\n"
            "- **Why a simple cutoff was not enough**, **How the threshold was chosen**, "
            "**Is the threshold robust to rephrasing?**, and **Measuring the coverage "
            "check** — the full story of the refuse-or-answer decision.\n"
        ),
        tr=(
            "Bu sekmedeki diğer raporlar bunların her birini açıyor:\n\n"
            "- **Metni nasıl bölmeli?** — yukarıdaki sayıların arkasındaki karşılaştırma.\n"
            "- **Aramanın yanıldığı yerler** — en kötü sıraladığı sorular ve "
            "arkalarındaki iki örüntü.\n"
            "- **Hibrit arama** ve **Yeniden sıralama** — reddedilen iki fikir ve "
            "ölçümleri.\n"
            "- **Basit eşik neden yetmedi**, **Eşik nasıl belirlendi**, **Eşik farklı "
            "ifadelere dayanıklı mı?** ve **Kapsam denetiminin ölçümü** — cevapla-ya da "
            "reddet kararının tüm hikayesi.\n"
        ),
    )

    written = report.write(RESULTS_DIR, "summary")
    print("Written:")
    for p in written:
        print(f"  {p}")


if __name__ == "__main__":
    main()
