# How Was the Cutoff Chosen?

The system refuses to answer when a question looks like something the notes do not cover. That decision comes down to one number: a score, and a cutoff below which the question is turned away.

Picking that cutoff by eye is easy to get wrong — the first attempt was set just below the lowest score a real question had produced, which looked safe on the questions it was chosen from and let a quarter of unrelated questions through in practice. This report picks it by stating what a mistake costs and letting the data settle the rest.

Measured on 47 questions the notes do cover and 33 they do not. Two kinds of mistake, weighted differently: answering an out-of-scope question counts 2.0, refusing a real one counts 1.0 — a wrong answer costs more than an unnecessary refusal, because someone can rephrase a refusal but cannot tell that a confident answer is wrong.

1 of these came from decisions corrected through the dashboard — real questions the system got wrong in use, rather than invented test cases.

## The cutoff the data picks

Trying every possible cutoff and keeping the one with the lowest total cost gives **-3.68**. At that setting 2 out-of-scope questions get answered and 2 real ones get refused.

## Does it hold up on questions it was not chosen from?

A cutoff tuned on a set of questions will always look good on that same set. To get an honest figure, the questions are split into 5 groups: the cutoff is fitted on 4 of them and tested on the one left out, 5 times over. Every error below is on a question the cutoff had never seen.

| round | cutoff fitted on the others | out-of-scope answered | real questions refused |
|---|---|---|---|
| 1 | -2.99 | 0 | 3 |
| 2 | -3.68 | 1 | 0 |
| 3 | -3.68 | 1 | 0 |
| 4 | -3.94 | 1 | 1 |
| 5 | -3.68 | 0 | 1 |
| **total** | average -3.59 | **3 of 33** | **5 of 47** |

The cutoff lands between -3.94 and -2.99 whichever questions are held out — it is following the shape of the data, not balancing on any one question.

## What if a wrong answer were judged differently?

Weighting a wrong answer twice as heavily as an unnecessary refusal is a judgement call. Here is what the same procedure returns under other weightings, so the choice can be seen rather than assumed.

| wrong answer weighed against wrong refusal | cutoff | out-of-scope answered | real questions refused |
|---|---|---|---|
| 1:1 | -3.68 | 2/33 | 2/47 |
| 2:1 ← | -3.68 | 2/33 | 2/47 |
| 3:1 | -3.68 | 2/33 | 2/47 |
| 5:1 | -3.08 | 2/33 | 6/47 |
| 10:1 | -0.63 | 0/33 | 15/47 |

The arrow marks the setting in use. Weighting the two mistakes equally, or a wrong answer three times as heavily, gives the same cutoff — the choice is not balanced on that judgement.

## Turning the score into a percentage

The raw score means nothing on its own — is -3.68 close or far? Fitting a small curve to the scores converts them into something readable: the chance that a question is covered. The cutoff can then be stated as "answer above 50% confidence" instead of a bare number.

| confidence cutoff | same as raw score | out-of-scope answered | real questions refused |
|---|---|---|---|
| 30% | -4.66 | 6/33 | 2/47 |
| 50% | -3.58 | 2/33 | 3/47 |
| 70% | -2.50 | 2/33 | 7/47 |
| 90% | -0.79 | 1/33 | 15/47 |
### Do the percentages mean what they say?

Grouping questions by the confidence they were given, and checking how many of each group really were covered. The last two columns should track each other.

| confidence given | questions | average confidence | actually covered |
|---|---|---|---|
| 0–20% | 25 | 7% | 4% |
| 20–40% | 7 | 29% | 14% |
| 40–60% | 5 | 50% | 80% |
| 60–80% | 7 | 73% | 86% |
| 80–100% | 36 | 97% | 97% |

Each group holds only a handful of questions, so this is a sanity check rather than a precise measurement — but the two columns move together, which is what it should look like.
