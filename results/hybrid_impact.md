# Hybrid Search: Tested and Rejected

The system finds sources by meaning: a question and a passage are each turned into a list of numbers, and the closest ones are returned. That handles rephrasing well, but can miss an exact term. Keyword search has the opposite profile — it matches exact words and nothing else.

Combining the two is standard advice, on the theory that each covers the other's blind spot. This measures whether it actually helps here.

Measured on 47 questions, `by_heading` index.

## The three approaches

| method | correct source ranked 1st | in top 3 | in top 5 | ranking quality |
|---|---|---|---|---|
| meaning-based search only | **0.809** | 0.936 | 0.936 | **0.865** |
| the two mixed evenly | 0.723 | 0.872 | 0.915 | 0.798 |
| keyword search only | 0.638 | 0.809 | 0.872 | 0.727 |

The first column is the share of questions whose correct source was ranked first — the measure that matters most, since people read the top result. Meaning-based search reaches 0.809, keyword search 0.638, and mixing them lands below the better of the two rather than above it.

## Does a different mix help?

Weight 1.0 means meaning-based search only; lower values give keyword search more say.

| weight on meaning-based search | correct source ranked 1st | in top 3 | in top 5 | ranking quality |
|---|---|---|---|---|
| 1.0 (meaning only) | **0.809** | 0.936 | 0.936 | **0.865** |
| 0.3 | 0.702 | 0.851 | 0.915 | 0.784 |
| 0.5 | 0.723 | 0.872 | 0.915 | 0.798 |
| 0.7 | 0.745 | 0.915 | 0.936 | 0.827 |
| 0.9 | 0.766 | 0.936 | 0.936 | 0.844 |
## Why it does not help here

No mix beats meaning-based search on its own. The closest is a weight of 0.9 at 0.766, still short of 0.809.

The reason is the corpus. Keyword search earns its place when documents contain rare, exact strings — product codes, error numbers, unusual names. These notes are the opposite: a few dozen pages that all share the same machine-learning vocabulary. Nearly every page mentions "model", "veri", "metrik", so matching on those words separates almost nothing, and mixing that signal in only dilutes a stronger one.

The result was measured, not assumed, and the code was left unchanged: `query.py` still uses meaning-based search alone.
