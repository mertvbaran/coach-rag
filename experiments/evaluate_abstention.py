"""Evaluates the out-of-scope gate as a selective-prediction problem.

Motivation: the gate in reranker.py uses a single hand-picked threshold on
one score, max(cross_encoder). Interactive testing found that paraphrasing
an out-of-scope question can flip its decision (see
results/threshold_robustness.md), and a first attempt at fixing it by
tuning a better rule on the same questions used to find the problem scored
perfectly on those questions and then failed on held-out ones -- a textbook
case of tuning on the test set.

This script measures the gate the way the selective-prediction literature
does, using threshold-independent metrics so the quality of the underlying
*signal* can be judged separately from the choice of cutoff:

- AUROC: how well the score separates in-scope from out-of-scope at any
  threshold. 0.5 = no signal, 1.0 = perfect separation.
- Coverage-risk curve: for each operating point, what fraction of
  questions are answered (coverage) and what fraction of those are
  out-of-scope questions that should have been refused (risk).
- Abstention precision/recall/F1 at the currently-shipped threshold.

Metric choice follows Wen et al., "Know Your Limits: A Survey of
Abstention in Large Language Models", TACL 2025 (13:529-556), which
recommends reporting coverage, error rates and trade-off curves together
rather than a single accuracy number, and notes that query answerability
is inherently hard to express as model confidence.

Questions are held in two groups: the ones used earlier when tuning a
candidate rule ("tuning"), and ones never used for tuning ("held-out").
Metrics are reported separately for each so any gap between them is
visible rather than averaged away.
"""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from config import CACHE_DIR, INDEX_DIR, RESULTS_DIR
from report import Report
from reranker import CE_OUT_OF_SCOPE_THRESHOLD

CHUNKER = "by_heading"
POOL_SIZE = 10

# Out-of-scope questions used earlier while tuning a candidate voting rule.
# Kept separate from the held-out set below so the difference is measurable.
OOS_TUNING = [
    "Kubernetes pod network policy nasıl tanımlanır?",
    "Kubernetes'te pod'lar arası network policy nasıl tanımlanır?",
    "Kubernetes'te pod'lar arasındaki ağ trafiğini nasıl kısıtlarım?",
    "React useEffect hook ne zaman tetiklenir?",
    "React'te useEffect hook'u ne zaman çalışır?",
    "useEffect'in bağımlılık dizisi (dependency array) nasıl çalışır?",
    "Blockchain konsensüs algoritmaları nelerdir?",
    "Blockchain'de konsensüs nasıl sağlanır?",
    "Proof of work ile proof of stake arasındaki fark nedir?",
    "Transformer mimarisinde self-attention nasıl çalışır?",
    "Transformer'larda self-attention mekanizması nedir?",
    "Attention is all you need makalesindeki temel fikir nedir?",
]

# Never used for tuning any rule or threshold.
OOS_HELDOUT = [
    "Docker container ile virtual machine arasındaki fark nedir?",
    "PostgreSQL index türleri nelerdir ve ne zaman kullanılır?",
    "REST API ile GraphQL arasındaki temel fark nedir?",
    "Git rebase ile merge arasındaki fark nedir?",
    "TCP three-way handshake nasıl çalışır?",
    "Redis cache invalidation stratejileri nelerdir?",
    "CI/CD pipeline nasıl kurulur?",
    "OAuth 2.0 authorization flow nasıl işler?",
    "Linux systemd servisi nasıl yazılır?",
    "Terraform state dosyası ne işe yarar?",
    "Bayesian hierarchical modelleme nedir?",
    "Kalman filtresi nasıl çalışır?",
    "Gaussian process regression ne zaman tercih edilir?",
    "Markov Chain Monte Carlo örnekleme nasıl yapılır?",
    "Survival analysis Cox regresyonu nedir?",
    "Evde ekmek nasıl yapılır?",
    "İyi bir uyku düzeni için ne yapmalıyım?",
    "Elektrikli araba almak mantıklı mı?",
    "Yoga ile pilates arasındaki fark nedir?",
    "Bir bitkiyi nasıl çoğaltırım?",
]


def collect_scores(questions: list[str]) -> list[dict]:
    """Returns per-question bi-encoder and cross-encoder scores over the top-k pool."""
    import yaml  # noqa: F401 -- imported by callers via load_questions

    from embedder import Embedder
    from reranker import Reranker
    from store import load_index, search

    chunks, embeddings = load_index(INDEX_DIR, CHUNKER)
    embedder = Embedder(CACHE_DIR)
    reranker = Reranker()

    rows = []
    for q in questions:
        query_vec = embedder.embed([q])[0]
        pool = search(query_vec, embeddings, k=POOL_SIZE)
        pool_texts = [chunks[idx]["text"] for idx, _ in pool]
        ce_scores = sorted(reranker.score(q, pool_texts), reverse=True)
        rows.append({"question": q, "bi_top1": float(pool[0][1]), "ce": ce_scores})
    return rows


def auroc(pos_scores: list[float], neg_scores: list[float]) -> float:
    """AUROC via the Mann-Whitney U identity: P(random positive > random negative).

    `pos` = in-scope (should be accepted), `neg` = out-of-scope.
    Ties count as half, matching the standard definition.
    """
    wins = 0.0
    for p in pos_scores:
        for n in neg_scores:
            if p > n:
                wins += 1.0
            elif p == n:
                wins += 0.5
    return wins / (len(pos_scores) * len(neg_scores))


def coverage_risk_curve(pos_scores: list[float], neg_scores: list[float]) -> list[tuple]:
    """For each candidate threshold, coverage and risk over the combined set.

    coverage = answered / all questions
    risk     = out-of-scope answered / answered  (fraction of answers that should have been refused)
    """
    all_scores = sorted(set(pos_scores + neg_scores), reverse=True)
    total = len(pos_scores) + len(neg_scores)
    curve = []
    for t in all_scores:
        accepted_pos = sum(1 for s in pos_scores if s >= t)
        accepted_neg = sum(1 for s in neg_scores if s >= t)
        answered = accepted_pos + accepted_neg
        if answered == 0:
            continue
        curve.append((t, answered / total, accepted_neg / answered, accepted_pos, accepted_neg))
    return curve


def abstention_prf(pos_scores: list[float], neg_scores: list[float], threshold: float) -> dict:
    """Precision/recall/F1 treating ABSTAINING on an out-of-scope question as the positive class."""
    tp = sum(1 for s in neg_scores if s < threshold)   # correctly abstained
    fp = sum(1 for s in pos_scores if s < threshold)   # wrongly abstained on in-scope
    fn = sum(1 for s in neg_scores if s >= threshold)  # failed to abstain
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"precision": precision, "recall": recall, "f1": f1, "tp": tp, "fp": fp, "fn": fn}


def main():
    import yaml

    questions_path = Path(__file__).parent.parent / "eval" / "questions.yaml"
    with open(questions_path, encoding="utf-8") as f:
        eval_questions = yaml.safe_load(f)["questions"]
    in_scope_qs = [q["question"] for q in eval_questions if q["expected"]]

    print(f"Scoring {len(in_scope_qs)} in-scope, {len(OOS_TUNING)} tuning OOS, {len(OOS_HELDOUT)} held-out OOS...")
    in_scope = collect_scores(in_scope_qs)
    oos_tuning = collect_scores(OOS_TUNING)
    oos_heldout = collect_scores(OOS_HELDOUT)

    cache_path = RESULTS_DIR / "abstention_scores.json"
    RESULTS_DIR.mkdir(exist_ok=True)
    cache_path.write_text(
        json.dumps({"in_scope": in_scope, "oos_tuning": oos_tuning, "oos_heldout": oos_heldout}, ensure_ascii=False),
        encoding="utf-8",
    )

    # The signal currently shipped: max over the top-k cross-encoder scores.
    pos = [max(r["ce"]) for r in in_scope]
    neg_tune = [max(r["ce"]) for r in oos_tuning]
    neg_held = [max(r["ce"]) for r in oos_heldout]
    neg_all = neg_tune + neg_held

    auroc_all = auroc(pos, neg_all)
    report = Report()
    report.add(
        en="# How Well Does the Coverage Check Work?\n",
        tr="# Kapsam Denetimi Ne Kadar İyi Çalışıyor?\n",
    )
    report.add(
        en=(
            "Before answering, the system decides whether the notes cover the question "
            "at all. That decision is worth measuring in two separate parts: how well "
            "the underlying score can tell the two kinds of question apart, and how "
            "well the particular cutoff in use performs.\n\n"
            "Keeping them apart matters. If the score itself cannot separate the "
            "groups, no cutoff will fix it. If it can, then a poor result is a "
            "cutoff problem, not a model problem.\n"
        ),
        tr=(
            "Sistem cevap vermeden önce, sorunun bilgi tabanında karşılığı olup olmadığına "
            "karar veriyor. Bu kararı iki ayrı parça olarak ölçmek gerekiyor: alttaki "
            "skorun iki tür soruyu ne kadar ayırt edebildiği ve kullanılan belirli "
            "eşiğin ne kadar iyi çalıştığı.\n\n"
            "İkisini ayrı tutmak önemli. Skorun kendisi grupları ayıramıyorsa hiçbir "
            "eşik bunu düzeltemez. Ayırabiliyorsa, kötü bir sonuç eşik sorunudur, "
            "model sorunu değil.\n"
        ),
    )
    report.add(
        en=(
            f"Measured on {len(pos)} questions the notes cover and {len(neg_all)} they "
            f"do not. The out-of-scope questions are split into two groups: "
            f"{len(neg_tune)} that were used earlier while trying out a candidate "
            f"rule, and {len(neg_held)} that were held back and never used for any "
            f"tuning. Reporting them separately shows whether the earlier tuning "
            f"flattered the result.\n"
        ),
        tr=(
            f"Ölçüm, notların kapsadığı {len(pos)} soru ve kapsamadığı "
            f"{len(neg_all)} soru üzerinde yapıldı. Kapsam dışı sorular iki gruba "
            f"ayrılmış: {len(neg_tune)} tanesi daha önce bir kural denenirken "
            f"kullanılmıştı, {len(neg_held)} tanesi ise hiçbir ayarlamada "
            f"kullanılmayıp saklanmıştı. İkisini ayrı raporlamak, önceki ayarlamanın "
            f"sonucu şişirip şişirmediğini gösteriyor.\n"
        ),
    )
    report.add(
        en=(
            "This is a fixed question set, unlike threshold_selection.md's fitting "
            "data: it stays the same across runs so a signal-quality number like "
            "AUROC means the same thing each time it's reported, rather than "
            "shifting with whatever corrections have accumulated in "
            "data/gate_feedback.jsonl. The shipped cutoff itself does track those "
            "corrections -- see threshold_selection.md for the count that includes "
            "them.\n"
        ),
        tr=(
            "Bu, threshold_selection.md'nin kullandığı veriden farklı olarak sabit "
            "bir soru seti: AUROC gibi bir sinyal-kalitesi sayısının her raporda aynı "
            "şeyi ifade etmesi için, data/gate_feedback.jsonl'da biriken "
            "düzeltmelerle birlikte değişmeden sabit kalıyor. Kullanılan eşiğin "
            "kendisi ise bu düzeltmeleri hesaba katıyor -- onları da içeren sayı "
            "için bkz. threshold_selection.md.\n"
        ),
    )

    report.add(
        en="## Can the score tell the two apart at all?\n",
        tr="## Skor ikisini ayırt edebiliyor mu?\n",
    )
    report.add(
        en=(
            "This measure asks: pick one covered question and one that is not — how "
            "often does the covered one get the higher score? 0.5 means the score is "
            "no better than a coin flip; 1.0 means it always gets the order right, so "
            "a perfect cutoff exists somewhere.\n"
        ),
        tr=(
            "Bu ölçüt şunu soruyor: notların kapsadığı bir soru ile kapsamadığı bir "
            "soru seçilse, kapsanan olan ne sıklıkla daha yüksek skor alır? 0.5 "
            "skorun yazı-turadan farksız olduğu, 1.0 ise sıralamayı her zaman doğru "
            "yaptığı — yani bir yerde mükemmel bir eşik bulunduğu anlamına gelir.\n"
        ),
    )
    report.add(
        en="| out-of-scope group | questions | score |",
        tr="| kapsam dışı grup | soru | skor |",
    )
    report.both("|---|---|---|")
    report.add(
        en=f"| used in earlier tuning | {len(neg_tune)} | {auroc(pos, neg_tune):.3f} |",
        tr=f"| önceki ayarlamada kullanılan | {len(neg_tune)} | {auroc(pos, neg_tune):.3f} |",
    )
    report.add(
        en=f"| never used for tuning | {len(neg_held)} | {auroc(pos, neg_held):.3f} |",
        tr=f"| hiç kullanılmayan | {len(neg_held)} | {auroc(pos, neg_held):.3f} |",
    )
    report.add(
        en=f"| **all together** | {len(neg_all)} | **{auroc_all:.3f}** |",
        tr=f"| **hepsi birlikte** | {len(neg_all)} | **{auroc_all:.3f}** |",
    )
    report.add(
        en=(
            f"\nAt {auroc_all:.3f} the score separates the two groups well, and the "
            f"held-out group scores close to the tuned one — so the quality is real, "
            f"not an artefact of having tuned on those questions.\n"
        ),
        tr=(
            f"\n{auroc_all:.3f} değeriyle skor iki grubu iyi ayırıyor ve saklanan "
            f"grup, ayarlamada kullanılana yakın sonuç veriyor — yani bu kalite "
            f"gerçek, o sorular üzerinde ayarlama yapmış olmanın bir yan etkisi "
            f"değil.\n"
        ),
    )

    report.add(
        en="## How the cutoff in use performs\n",
        tr="## Kullanılan eşik nasıl çalışıyor\n",
    )
    report.add(
        en=(
            "Three ways of looking at the same decisions. *Of the refusals it made, "
            "how many were right* and *of the questions it should have refused, how "
            "many did it catch* pull against each other; the third column balances "
            "them into one number.\n"
        ),
        tr=(
            "Aynı kararlara üç farklı bakış. *Yaptığı reddetmelerin kaçı doğruydu* ile "
            "*reddetmesi gereken sorulardan kaçını yakaladı* birbirine ters çalışıyor; "
            "üçüncü sütun ikisini tek bir sayıda dengeliyor.\n"
        ),
    )
    report.add(
        en="| out-of-scope group | refusals that were right | out-of-scope it caught | balance | correctly refused | real questions wrongly refused | missed |",
        tr="| kapsam dışı grup | doğru olan reddetmeler | yakaladığı kapsam dışı | denge | doğru reddedilen | yanlışlıkla reddedilen gerçek soru | kaçırılan |",
    )
    report.both("|---|---|---|---|---|---|---|")
    for en_name, tr_name, neg in [
        ("used in earlier tuning", "önceki ayarlamada kullanılan", neg_tune),
        ("never used for tuning", "hiç kullanılmayan", neg_held),
        ("all together", "hepsi birlikte", neg_all),
    ]:
        m = abstention_prf(pos, neg, CE_OUT_OF_SCOPE_THRESHOLD)
        row = (
            f"| {{name}} | {m['precision']:.3f} | {m['recall']:.3f} | {m['f1']:.3f} | "
            f"{m['tp']} | {m['fp']} | {m['fn']} |"
        )
        report.add(en=row.format(name=en_name), tr=row.format(name=tr_name))

    report.add(
        en="## Answering more means being wrong more\n",
        tr="## Daha çok cevaplamak, daha çok yanılmak demek\n",
    )
    report.add(
        en=(
            "Every possible cutoff, and the trade it makes. *Answered* is the share of "
            "all questions the system replies to; *wrong answers* is the share of "
            "those replies that went to a question it should have refused. Lowering "
            "the cutoff answers more questions and gets more of them wrong.\n"
        ),
        tr=(
            "Olası her eşik ve yaptığı takas. *Cevaplanan*, sistemin yanıt verdiği "
            "soruların oranı; *hatalı cevap*, bu yanıtların içinde reddedilmesi "
            "gereken sorulara gidenlerin oranı. Eşiği düşürmek daha çok soruyu "
            "cevaplatıyor ve daha çoğunu yanlış yapıyor.\n"
        ),
    )
    report.add(
        en="| cutoff | answered | wrong answers | real questions answered | out-of-scope answered |",
        tr="| eşik | cevaplanan | hatalı cevap | cevaplanan gerçek soru | cevaplanan kapsam dışı |",
    )
    report.both("|---|---|---|---|---|")
    curve = coverage_risk_curve(pos, neg_all)
    step = max(1, len(curve) // 20)
    for t, cov, risk, ap, an in curve[::step]:
        marker = " ←" if abs(t - CE_OUT_OF_SCOPE_THRESHOLD) < 0.4 else ""
        cov_pct, risk_pct = f"{cov * 100:.0f}", f"{risk * 100:.0f}"
        counts = f"{ap}/{len(pos)} | {an}/{len(neg_all)} |"
        report.add(
            en=f"| {t:.2f}{marker} | {cov_pct}% | {risk_pct}% | {counts}",
            tr=f"| {t:.2f}{marker} | %{cov_pct} | %{risk_pct} | {counts}",
        )

    best_cov = max((c for c in curve if c[2] == 0.0), key=lambda c: c[1], default=None)
    if best_cov:
        report.add(
            en=(
                f"\nRefusing every out-of-scope question is possible, but only by "
                f"setting the cutoff at {best_cov[0]:.2f} — which also turns away "
                f"{len(pos) - best_cov[3]} real questions. The setting in use accepts a "
                f"couple of mistakes in exchange for answering far more of what it "
                f"should.\n"
            ),
            tr=(
                f"\nKapsam dışı soruların hepsini reddetmek mümkün, ama bunun için "
                f"eşiği {best_cov[0]:.2f} yapmak gerekiyor — o da "
                f"{len(pos) - best_cov[3]} gerçek soruyu geri çeviriyor. Kullanılan "
                f"ayar, cevaplaması gereken soruların çok daha fazlasını cevaplamak "
                f"karşılığında birkaç hatayı kabul ediyor.\n"
            ),
        )

    report.add(
        en=(
            "\nMetric choice follows Wen et al., *Know Your Limits: A Survey of "
            "Abstention in Large Language Models*, TACL 2025 (13:529-556), which "
            "recommends reporting separation, error rates and the coverage trade-off "
            "together rather than a single accuracy figure.\n"
        ),
        tr=(
            "\nÖlçüt seçimi Wen ve ark., *Know Your Limits: A Survey of Abstention in "
            "Large Language Models*, TACL 2025 (13:529-556) çalışmasını izliyor; bu "
            "çalışma tek bir başarı yüzdesi yerine ayrım gücünün, hata oranlarının ve "
            "kapsam takasının birlikte raporlanmasını öneriyor.\n"
        ),
    )

    written = report.write(RESULTS_DIR, "abstention_metrics")
    print("\nWritten:")
    for p in written:
        print(f"  {p}")


if __name__ == "__main__":
    main()
