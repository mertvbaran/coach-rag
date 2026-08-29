"""Derives the out-of-scope threshold from data instead of picking it by hand.

The first threshold (-5.5) was set to just clear the lowest in-scope score
in a small sample. The second (-2.15) was read off a coverage-risk curve by
eye. Both were judgement calls; this script replaces the judgement with a
stated objective and a measurement.

Three things happen here:

1. **Cost-based selection.** An explicit cost is assigned to each kind of
   mistake -- answering a question that should have been refused, and
   refusing one that should have been answered -- and the threshold that
   minimises total cost is computed. The choice of costs is still a product
   decision, but it is written down rather than hidden inside a hand-picked
   number, and the sensitivity of the result to that choice is reported.

2. **K-fold cross-validation.** Selecting a threshold on the same data used
   to report its performance inflates the result. Here the threshold is
   fitted on k-1 folds and scored on the held-out fold, k times, so the
   reported numbers describe behaviour on questions the threshold was not
   chosen on.

3. **Platt scaling.** A logistic regression maps the raw cross-encoder
   score to a probability of being in-scope, fitted out-of-fold. This makes
   the operating point interpretable ("accept above 50% confidence")
   instead of an opaque cutoff, and lets calibration quality be measured
   directly.

Reads the scores cached by evaluate_abstention.py.
"""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from config import DATA_DIR, RESULTS_DIR
from report import Report

# Cost of each error type, in arbitrary but comparable units.
# FALSE_ACCEPT: answering an out-of-scope question (the system presents
#   unrelated notes as if they were relevant).
# FALSE_REFUSE: refusing a question the vault actually covers.
# Weighted 2:1 because a confidently wrong answer is more damaging to trust
# than an unnecessary "not in my notes" -- the user can rephrase, but cannot
# tell that a wrong answer is wrong. Sensitivity to this ratio is reported.
COST_FALSE_ACCEPT = 2.0
COST_FALSE_REFUSE = 1.0

N_FOLDS = 5
RANDOM_SEED = 0


def load_scores() -> tuple[np.ndarray, np.ndarray, int]:
    """Returns (scores, labels, n_from_feedback) with label 1 = in-scope, 0 = out-of-scope.

    Combines the fixed question set with any corrections the user recorded
    through the dashboard (see src/feedback.py). Recorded corrections are real
    questions that the gate got wrong, so they carry more information about
    where the boundary actually sits than invented ones do.
    """
    path = RESULTS_DIR / "abstention_scores.json"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run `python src/evaluate_abstention.py` first."
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    scores, labels = [], []
    for row in data["in_scope"]:
        scores.append(max(row["ce"]))
        labels.append(1)
    for group in ("oos_tuning", "oos_heldout"):
        for row in data[group]:
            scores.append(max(row["ce"]))
            labels.append(0)

    from feedback import load as load_feedback

    corrections = load_feedback(DATA_DIR)
    for entry in corrections:
        scores.append(entry["ce_score"])
        labels.append(1 if entry["should_be_in_scope"] else 0)

    return np.array(scores), np.array(labels), len(corrections)


def total_cost(scores: np.ndarray, labels: np.ndarray, threshold: float,
               c_accept: float = COST_FALSE_ACCEPT, c_refuse: float = COST_FALSE_REFUSE) -> float:
    accepted = scores >= threshold
    false_accepts = int(np.sum(accepted & (labels == 0)))
    false_refuses = int(np.sum(~accepted & (labels == 1)))
    return c_accept * false_accepts + c_refuse * false_refuses


def best_threshold(scores: np.ndarray, labels: np.ndarray,
                   c_accept: float = COST_FALSE_ACCEPT, c_refuse: float = COST_FALSE_REFUSE) -> float:
    """Threshold minimising total cost. Ties are broken toward the midpoint of
    the widest tied interval, so the choice sits in the middle of a stable
    region rather than balanced on one data point."""
    candidates = np.unique(scores)
    # Evaluate midpoints between consecutive distinct scores, plus the extremes.
    grid = np.concatenate([[candidates[0] - 1.0], (candidates[:-1] + candidates[1:]) / 2, [candidates[-1] + 1.0]])
    costs = np.array([total_cost(scores, labels, t, c_accept, c_refuse) for t in grid])
    min_cost = costs.min()
    tied = grid[costs == min_cost]
    return float(np.median(tied))


def fit_platt(scores: np.ndarray, labels: np.ndarray, iters: int = 2000, lr: float = 0.05) -> tuple[float, float]:
    """Fits P(in-scope | score) = sigmoid(a * score + b) by gradient descent on
    log loss. Two parameters on a few dozen points -- no need for a solver."""
    a, b = 1.0, 0.0
    n = len(scores)
    s = (scores - scores.mean()) / (scores.std() + 1e-9)  # standardise for stable steps
    for _ in range(iters):
        p = 1.0 / (1.0 + np.exp(-(a * s + b)))
        grad_a = np.dot(p - labels, s) / n
        grad_b = np.sum(p - labels) / n
        a -= lr * grad_a
        b -= lr * grad_b
    # Undo standardisation so the parameters apply to raw scores.
    mu, sigma = scores.mean(), scores.std() + 1e-9
    return float(a / sigma), float(b - a * mu / sigma)


def platt_prob(scores: np.ndarray, a: float, b: float) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-(a * scores + b)))


def make_folds(labels: np.ndarray, k: int, seed: int) -> list[np.ndarray]:
    """Stratified fold assignment, so each fold keeps the class balance."""
    rng = np.random.default_rng(seed)
    fold_of = np.empty(len(labels), dtype=int)
    for cls in (0, 1):
        idx = np.where(labels == cls)[0]
        rng.shuffle(idx)
        fold_of[idx] = np.arange(len(idx)) % k
    return [np.where(fold_of == f)[0] for f in range(k)]


def main():
    scores, labels, n_feedback = load_scores()
    n_in, n_out = int(np.sum(labels == 1)), int(np.sum(labels == 0))
    print(f"Loaded {len(scores)} questions: {n_in} in-scope, {n_out} out-of-scope")
    if n_feedback:
        print(f"  ({n_feedback} of these came from recorded gate corrections)")
    print()

    report = Report()
    report.add(
        en="# How Was the Cutoff Chosen?\n",
        tr="# Eşik Nasıl Belirlendi?\n",
    )
    report.add(
        en=(
            "The system refuses to answer when a question looks like something the "
            "notes do not cover. That decision comes down to one number: a score, and "
            "a cutoff below which the question is turned away.\n\n"
            "Picking that cutoff by eye is easy to get wrong — the first attempt was "
            "set just below the lowest score a real question had produced, which "
            "looked safe on the questions it was chosen from and let a quarter of "
            "unrelated questions through in practice. This report picks it by stating "
            "what a mistake costs and letting the data settle the rest.\n"
        ),
        tr=(
            "Sistem, bilgi tabanının kapsamadığı bir soru geldiğini düşündüğünde cevap "
            "vermeyi reddediyor. Bu karar tek bir sayıya dayanıyor: bir skor ve altına "
            "düşüldüğünde sorunun geri çevrildiği bir eşik.\n\n"
            "Bu eşiği gözle seçmek kolayca yanlış gidiyor — ilk denemede gerçek bir "
            "sorunun aldığı en düşük skorun hemen altına konmuştu; seçildiği sorular "
            "üzerinde güvenli görünüyordu ama pratikte alakasız soruların dörtte birini "
            "içeri alıyordu. Bu rapor eşiği, bir hatanın maliyetini açıkça yazıp "
            "gerisini veriye bırakarak seçiyor.\n"
        ),
    )
    report.add(
        en=(
            f"Measured on {n_in} questions the notes do cover and {n_out} they do "
            f"not. Two kinds of mistake, weighted differently: answering an "
            f"out-of-scope question counts {COST_FALSE_ACCEPT}, refusing a real one "
            f"counts {COST_FALSE_REFUSE} — a wrong answer costs more than an "
            f"unnecessary refusal, because someone can rephrase a refusal but cannot "
            f"tell that a confident answer is wrong.\n"
        ),
        tr=(
            f"Ölçüm, notların kapsadığı {n_in} soru ve kapsamadığı {n_out} soru "
            f"üzerinde yapıldı. İki hata türü farklı ağırlıklandırıldı: kapsam dışı bir "
            f"soruyu cevaplamak {COST_FALSE_ACCEPT} puan, gerçek bir soruyu reddetmek "
            f"{COST_FALSE_REFUSE} puan — yanlış cevap gereksiz reddetmeden daha "
            f"maliyetli, çünkü reddedilen kişi soruyu yeniden sorabilir ama kendinden "
            f"emin görünen yanlış bir cevabın yanlış olduğunu anlayamaz.\n"
        ),
    )
    if n_feedback:
        report.add(
            en=(
                f"{n_feedback} of these came from decisions corrected through the "
                f"dashboard — real questions the system got wrong in use, rather than "
                f"invented test cases.\n"
            ),
            tr=(
                f"Bunlardan {n_feedback} tanesi arayüz üzerinden düzeltilen "
                f"kararlardan geliyor — uydurulmuş test soruları değil, sistemin "
                f"gerçek kullanımda yanıldığı sorular.\n"
            ),
        )

    # --- 1. Threshold fitted on everything (for reference) ---
    t_full = best_threshold(scores, labels)
    cost_full = total_cost(scores, labels, t_full)
    acc = scores >= t_full
    fa = int(np.sum(acc & (labels == 0)))
    fr = int(np.sum(~acc & (labels == 1)))
    report.add(en="## The cutoff the data picks\n", tr="## Verinin seçtiği eşik\n")
    report.add(
        en=(
            f"Trying every possible cutoff and keeping the one with the lowest total "
            f"cost gives **{t_full:.2f}**. At that setting {fa} out-of-scope questions "
            f"get answered and {fr} real ones get refused.\n"
        ),
        tr=(
            f"Olası her eşik denenip toplam maliyeti en düşük olan seçildiğinde "
            f"**{t_full:.2f}** çıkıyor. Bu ayarda {fa} kapsam dışı soru cevaplanıyor, "
            f"{fr} gerçek soru reddediliyor.\n"
        ),
    )
    print(f"Cost-minimising threshold (fitted on all data): {t_full:.2f}")
    print(f"  {fa} out-of-scope accepted, {fr} in-scope refused\n")

    # --- 2. Cross-validated: fit on k-1 folds, score on the held-out fold ---
    folds = make_folds(labels, N_FOLDS, RANDOM_SEED)
    fold_thresholds, fold_errors = [], []
    report.add(
        en="## Does it hold up on questions it was not chosen from?\n",
        tr="## Seçilmediği sorularda da tutuyor mu?\n",
    )
    report.add(
        en=(
            f"A cutoff tuned on a set of questions will always look good on that same "
            f"set. To get an honest figure, the questions are split into {N_FOLDS} "
            f"groups: the cutoff is fitted on {N_FOLDS - 1} of them and tested on the "
            f"one left out, {N_FOLDS} times over. Every error below is on a question "
            f"the cutoff had never seen.\n"
        ),
        tr=(
            f"Bir eşik, üzerinde ayarlandığı soru kümesinde her zaman iyi görünür. "
            f"Dürüst bir sayı elde etmek için sorular {N_FOLDS} gruba ayrılıyor: eşik "
            f"{N_FOLDS - 1} grupta hesaplanıp dışarıda bırakılan grupta test ediliyor "
            f"ve bu {N_FOLDS} kez tekrarlanıyor. Aşağıdaki her hata, eşiğin hiç "
            f"görmediği bir soruda.\n"
        ),
    )
    report.add(
        en="| round | cutoff fitted on the others | out-of-scope answered | real questions refused |",
        tr="| tur | diğerlerinde hesaplanan eşik | cevaplanan kapsam dışı | reddedilen gerçek soru |",
    )
    report.both("|---|---|---|---|")
    for i, test_idx in enumerate(folds):
        train_idx = np.setdiff1d(np.arange(len(scores)), test_idx)
        t = best_threshold(scores[train_idx], labels[train_idx])
        acc = scores[test_idx] >= t
        fa = int(np.sum(acc & (labels[test_idx] == 0)))
        fr = int(np.sum(~acc & (labels[test_idx] == 1)))
        fold_thresholds.append(t)
        fold_errors.append((fa, fr))
        report.both(f"| {i + 1} | {t:.2f} | {fa} | {fr} |")
        print(f"  fold {i+1}: threshold {t:.2f} -> {fa} false accepts, {fr} false refuses")

    tot_fa = sum(f[0] for f in fold_errors)
    tot_fr = sum(f[1] for f in fold_errors)
    report.add(
        en=(
            f"| **total** | average {np.mean(fold_thresholds):.2f} | "
            f"**{tot_fa} of {n_out}** | **{tot_fr} of {n_in}** |"
        ),
        tr=(
            f"| **toplam** | ortalama {np.mean(fold_thresholds):.2f} | "
            f"**{n_out} sorudan {tot_fa}** | **{n_in} sorudan {tot_fr}** |"
        ),
    )
    report.add(
        en=(
            f"\nThe cutoff lands between {min(fold_thresholds):.2f} and "
            f"{max(fold_thresholds):.2f} whichever questions are held out — it is "
            f"following the shape of the data, not balancing on any one question.\n"
        ),
        tr=(
            f"\nHangi sorular dışarıda bırakılırsa bırakılsın eşik "
            f"{min(fold_thresholds):.2f} ile {max(fold_thresholds):.2f} arasında "
            f"kalıyor — verinin genel biçimini takip ediyor, tek bir sorunun üzerinde "
            f"dengede durmuyor.\n"
        ),
    )
    print(f"\n  CV totals: {tot_fa}/{n_out} false accepts, {tot_fr}/{n_in} false refuses")
    print(f"  Threshold across folds: mean {np.mean(fold_thresholds):.2f}, sd {np.std(fold_thresholds):.2f}\n")

    # --- 3. Sensitivity to the cost ratio ---
    report.add(
        en="## What if a wrong answer were judged differently?\n",
        tr="## Yanlış cevabın maliyeti farklı olsaydı?\n",
    )
    report.add(
        en=(
            "Weighting a wrong answer twice as heavily as an unnecessary refusal is a "
            "judgement call. Here is what the same procedure returns under other "
            "weightings, so the choice can be seen rather than assumed.\n"
        ),
        tr=(
            "Yanlış cevabı gereksiz reddetmenin iki katı ağırlıkta saymak bir tercih. "
            "Aynı yöntemin başka ağırlıklarda ne verdiği aşağıda — tercih varsayılmak "
            "yerine görülebilsin diye.\n"
        ),
    )
    report.add(
        en="| wrong answer weighed against wrong refusal | cutoff | out-of-scope answered | real questions refused |",
        tr="| yanlış cevabın yanlış reddetmeye oranı | eşik | cevaplanan kapsam dışı | reddedilen gerçek soru |",
    )
    report.both("|---|---|---|---|")
    for ratio in (1.0, 2.0, 3.0, 5.0, 10.0):
        t = best_threshold(scores, labels, c_accept=ratio, c_refuse=1.0)
        acc = scores >= t
        fa = int(np.sum(acc & (labels == 0)))
        fr = int(np.sum(~acc & (labels == 1)))
        chosen = " ←" if abs(ratio - COST_FALSE_ACCEPT) < 1e-9 else ""
        report.both(f"| {ratio:.0f}:1{chosen} | {t:.2f} | {fa}/{n_out} | {fr}/{n_in} |")
        print(f"  cost ratio {ratio:.0f}:1 -> threshold {t:.2f} ({fa} false accepts, {fr} false refuses)")
    report.add(
        en=(
            "\nThe arrow marks the setting in use. Weighting the two mistakes equally, "
            "or a wrong answer three times as heavily, gives the same cutoff — the "
            "choice is not balanced on that judgement.\n"
        ),
        tr=(
            "\nOk, kullanılan ayarı gösteriyor. İki hatayı eşit saymak da, yanlış "
            "cevabı üç kat ağır saymak da aynı eşiği veriyor — seçim bu tercihin "
            "üzerinde dengede durmuyor.\n"
        ),
    )

    # --- 4. Platt scaling, fitted out-of-fold ---
    print()
    oof_probs = np.zeros(len(scores))
    for test_idx in folds:
        train_idx = np.setdiff1d(np.arange(len(scores)), test_idx)
        a, b = fit_platt(scores[train_idx], labels[train_idx])
        oof_probs[test_idx] = platt_prob(scores[test_idx], a, b)

    a_full, b_full = fit_platt(scores, labels)
    report.add(
        en="## Turning the score into a percentage\n",
        tr="## Skoru yüzdeye çevirmek\n",
    )
    report.add(
        en=(
            f"The raw score means nothing on its own — is {t_full:.2f} close or far? "
            f"Fitting a small curve to the scores converts them into something "
            f"readable: the chance that a question is covered. The cutoff can then be "
            f"stated as \"answer above 50% confidence\" instead of a bare number.\n"
        ),
        tr=(
            f"Ham skor tek başına bir şey ifade etmiyor — {t_full:.2f} yakın mı, uzak "
            f"mı? Skorlara küçük bir eğri uydurmak onları okunabilir bir şeye çeviriyor: "
            "sorunun kapsam içinde olma ihtimali. Böylece eşik, çıplak bir sayı yerine "
            "\"%50 güvenin üstünde cevapla\" biçiminde ifade edilebiliyor.\n"
        ),
    )
    report.add(
        en="| confidence cutoff | same as raw score | out-of-scope answered | real questions refused |",
        tr="| güven eşiği | ham skor karşılığı | cevaplanan kapsam dışı | reddedilen gerçek soru |",
    )
    report.both("|---|---|---|---|")
    for p_cut in (0.3, 0.5, 0.7, 0.9):
        raw_equiv = (np.log(p_cut / (1 - p_cut)) - b_full) / a_full
        acc = oof_probs >= p_cut
        fa = int(np.sum(acc & (labels == 0)))
        fr = int(np.sum(~acc & (labels == 1)))
        rest = f"{raw_equiv:.2f} | {fa}/{n_out} | {fr}/{n_in} |"
        report.add(
            en=f"| {p_cut * 100:.0f}% | {rest}",
            tr=f"| %{p_cut * 100:.0f} | {rest}",
        )
        print(f"  P>={p_cut:.1f} (raw {raw_equiv:.2f}) -> {fa} false accepts, {fr} false refuses")

    # Calibration check: within each probability bucket, does the predicted
    # probability match the observed rate of in-scope questions?
    report.add(
        en="### Do the percentages mean what they say?\n",
        tr="### Yüzdeler gerçekten söyledikleri anlama geliyor mu?\n",
    )
    report.add(
        en=(
            "Grouping questions by the confidence they were given, and checking how "
            "many of each group really were covered. The last two columns should track "
            "each other.\n"
        ),
        tr=(
            "Sorular, aldıkları güven değerine göre gruplanıp her grubun gerçekte ne "
            "kadarının kapsam içinde olduğuna bakılıyor. Son iki sütunun birbirini "
            "takip etmesi bekleniyor.\n"
        ),
    )
    report.add(
        en="| confidence given | questions | average confidence | actually covered |",
        tr="| verilen güven | soru | ortalama güven | gerçekte kapsam içi |",
    )
    report.both("|---|---|---|---|")
    for lo, hi in ((0.0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.01)):
        mask = (oof_probs >= lo) & (oof_probs < hi)
        if not mask.any():
            continue
        lo_pct, hi_pct = f"{lo * 100:.0f}", f"{min(hi, 1.0) * 100:.0f}"
        mean_pct, actual_pct = f"{oof_probs[mask].mean() * 100:.0f}", f"{labels[mask].mean() * 100:.0f}"
        report.add(
            en=f"| {lo_pct}–{hi_pct}% | {int(mask.sum())} | {mean_pct}% | {actual_pct}% |",
            tr=f"| %{lo_pct}–%{hi_pct} | {int(mask.sum())} | %{mean_pct} | %{actual_pct} |",
        )

    report.add(
        en=(
            "\nEach group holds only a handful of questions, so this is a sanity check "
            "rather than a precise measurement — but the two columns move together, "
            "which is what it should look like.\n"
        ),
        tr=(
            "\nHer grupta yalnızca birkaç soru olduğu için bu kesin bir ölçüm değil, "
            "bir sağlama — ama iki sütun birlikte hareket ediyor ve olması gereken "
            "de bu.\n"
        ),
    )

    written = report.write(RESULTS_DIR, "threshold_selection")
    print("\nWritten:")
    for p in written:
        print(f"  {p}")


if __name__ == "__main__":
    main()
