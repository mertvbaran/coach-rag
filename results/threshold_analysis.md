# Why Wasn't a Simple Cutoff Enough?

The search always returns something. Ask it about a topic the notes never cover and it still hands back its five closest guesses, with no sign that they are unrelated.

The obvious fix is a cutoff: every result carries a similarity score between 0 and 1, so refuse to answer when the best score is too low. This report tests whether any such cutoff actually works.

## How the scores are distributed

Three kinds of question, and the similarity score each one's best match received. If a cutoff is going to work, these groups have to separate.

| question type | count | lowest | highest | average |
|---|---|---|---|---|
| covered by the notes | 47 | 0.335 | 0.801 | 0.610 |
| out of scope, from the question set | 10 | 0.242 | 0.450 | 0.343 |
| out of scope, other technical fields | 4 | 0.339 | 0.444 | 0.391 |
| out of scope, everyday topics | 6 | 0.219 | 0.427 | 0.292 |

The ranges overlap. Questions the notes do cover go as low as 0.335, while unrelated technical questions reach 0.444 — so there is no line that cleanly separates them.

## Every cutoff, and what it costs

Two kinds of mistake pull in opposite directions: a strict cutoff turns away real questions, a loose one lets unrelated ones through.

| cutoff | real questions wrongly refused | unrelated questions wrongly accepted |
|---|---|---|
| 0.30 | 0/47 | 14/20 |
| 0.35 | 1/47 | 9/20 |
| 0.38 | 2/47 | 8/20 |
| 0.40 | 3/47 | 4/20 |
| 0.42 | 4/47 | 4/20 |
| 0.45 | 4/47 | 0/20 |
| 0.50 | 10/47 | 0/20 |
## What this means

**Everyday questions are easy to catch.** Weather, cooking, history — they share no vocabulary with the notes at all, so they score low and a cutoff turns them away reliably.

**Questions from other technical fields are not.** Kubernetes, React, Blockchain — these score in the same range as genuine questions, because they are written in the same register: technical prose, similar sentence shapes, overlapping words like "model", "sistem", "veri". One question about a food recipe even matched the recommendation-systems pages, because *tarif* and *öneri* sit close together in the model's view of meaning.

**So no single cutoff works.** Tightening it to shut out the technical questions starts refusing real ones; loosening it to let real ones through lets the technical ones in. Catching the hard cases needs a different signal, not a better number on the same one — which is what the report on *how the threshold was chosen* goes on to build.
