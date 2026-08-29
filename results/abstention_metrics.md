# How Well Does the Coverage Check Work?

Before answering, the system decides whether the notes cover the question at all. That decision is worth measuring in two separate parts: how well the underlying score can tell the two kinds of question apart, and how well the particular cutoff in use performs.

Keeping them apart matters. If the score itself cannot separate the groups, no cutoff will fix it. If it can, then a poor result is a cutoff problem, not a model problem.

Measured on 47 questions the notes cover and 32 they do not. The out-of-scope questions are split into two groups: 12 that were used earlier while trying out a candidate rule, and 20 that were held back and never used for any tuning. Reporting them separately shows whether the earlier tuning flattered the result.

This is a fixed question set, unlike threshold_selection.md's fitting data: it stays the same across runs so a signal-quality number like AUROC means the same thing each time it's reported, rather than shifting with whatever corrections have accumulated in data/gate_feedback.jsonl. The shipped cutoff itself does track those corrections -- see threshold_selection.md for the count that includes them.

## Can the score tell the two apart at all?

This measure asks: pick one covered question and one that is not — how often does the covered one get the higher score? 0.5 means the score is no better than a coin flip; 1.0 means it always gets the order right, so a perfect cutoff exists somewhere.

| out-of-scope group | questions | score |
|---|---|---|
| used in earlier tuning | 12 | 0.995 |
| never used for tuning | 20 | 0.969 |
| **all together** | 32 | **0.979** |

At 0.979 the score separates the two groups well, and the held-out group scores close to the tuned one — so the quality is real, not an artefact of having tuned on those questions.

## How the cutoff in use performs

Three ways of looking at the same decisions. *Of the refusals it made, how many were right* and *of the questions it should have refused, how many did it catch* pull against each other; the third column balances them into one number.

| out-of-scope group | refusals that were right | out-of-scope it caught | balance | correctly refused | real questions wrongly refused | missed |
|---|---|---|---|---|---|---|
| used in earlier tuning | 0.857 | 1.000 | 0.923 | 12 | 2 | 0 |
| never used for tuning | 0.900 | 0.900 | 0.900 | 18 | 2 | 2 |
| all together | 0.938 | 0.938 | 0.938 | 30 | 2 | 2 |
## Answering more means being wrong more

Every possible cutoff, and the trade it makes. *Answered* is the share of all questions the system replies to; *wrong answers* is the share of those replies that went to a question it should have refused. Lowering the cutoff answers more questions and gets more of them wrong.

| cutoff | answered | wrong answers | real questions answered | out-of-scope answered |
|---|---|---|---|---|
| 10.75 | 1% | 0% | 1/47 | 0/32 |
| 8.90 | 5% | 0% | 4/47 | 0/32 |
| 8.12 | 9% | 0% | 7/47 | 0/32 |
| 7.01 | 13% | 0% | 10/47 | 0/32 |
| 5.90 | 16% | 0% | 13/47 | 0/32 |
| 3.41 | 20% | 0% | 16/47 | 0/32 |
| 2.82 | 24% | 0% | 19/47 | 0/32 |
| 2.17 | 28% | 0% | 22/47 | 0/32 |
| 1.52 | 32% | 0% | 25/47 | 0/32 |
| 0.41 | 35% | 0% | 28/47 | 0/32 |
| -0.35 | 39% | 0% | 31/47 | 0/32 |
| -0.89 | 43% | 3% | 33/47 | 1/32 |
| -1.94 | 47% | 3% | 36/47 | 1/32 |
| -2.15 | 51% | 2% | 39/47 | 1/32 |
| -2.79 | 54% | 5% | 41/47 | 2/32 |
| -3.35 ← | 58% | 4% | 44/47 | 2/32 |
| -4.41 | 62% | 8% | 45/47 | 4/32 |
| -4.85 | 66% | 12% | 46/47 | 6/32 |
| -5.50 | 70% | 16% | 46/47 | 9/32 |
| -5.71 | 73% | 19% | 47/47 | 11/32 |
| -6.46 | 77% | 23% | 47/47 | 14/32 |
| -6.82 | 81% | 27% | 47/47 | 17/32 |
| -7.25 | 85% | 30% | 47/47 | 20/32 |
| -7.78 | 89% | 33% | 47/47 | 23/32 |
| -8.23 | 92% | 36% | 47/47 | 26/32 |
| -8.55 | 96% | 38% | 47/47 | 29/32 |
| -8.74 | 100% | 41% | 47/47 | 32/32 |

Refusing every out-of-scope question is possible, but only by setting the cutoff at -0.39 — which also turns away 15 real questions. The setting in use accepts a couple of mistakes in exchange for answering far more of what it should.


Metric choice follows Wen et al., *Know Your Limits: A Survey of Abstention in Large Language Models*, TACL 2025 (13:529-556), which recommends reporting separation, error rates and the coverage trade-off together rather than a single accuracy figure.
