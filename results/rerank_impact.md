# Re-ranking with a Second Model: Tested and Rejected

Search here works in one pass: every passage is turned into numbers ahead of time, and the ones closest to the question are returned. That is fast, but the comparison is indirect — question and passage are measured separately and only then compared.

A second kind of model reads the question and a passage *together* and judges how well they match. It is far slower, so it cannot score the whole collection, but it can re-order the top handful. The usual expectation is that this improves the ranking. This measures whether it does.

## Ranking quality, before and after re-ranking

An arrow pointing down means re-ranking made that measure worse.

| chunker | questions | correct source 1st: before → after | ranking quality: before → after |
|---|---|---|---|
| whole_doc | 47 | 0.745 → 0.745 → | 0.840 → 0.846 ↑ |
| by_heading | 47 | 0.809 → 0.596 ↓ | 0.870 → 0.762 ↓ |

**It makes things worse.** On the index the system actually uses, the share of questions answered correctly at rank 1 falls from 0.809 to 0.596.

Looking at which answers changed shows a consistent pattern: the second model prefers long, explanatory passages — flashcard-style question-and-answer pages and broad course summaries — over the short, focused page written about exactly that concept. In one case a question asks about "support, confidence, lift"; the page using those exact terms was ranked first by the original search, and the re-ranker pushed a general flashcard page above it.

That preference is not random. This kind of model is typically trained on web search data, where the better answer usually *is* the longer, more explanatory passage. These notes are the opposite: one idea per page, deliberately short. The model's training works against the way this collection is written.

## Where the second model does help

Re-ordering results is the wrong job for it. Deciding whether a question is covered at all turns out to be the right one.

Refusing to answer when its score falls below -3.68 correctly turns away 8 of 10 questions the notes have nothing to say about. The original search, using a simple similarity cutoff, catches 0 of 10.

So the model is used for exactly that and nothing else: the ranking is left alone, and the second model only decides whether to show a warning. Two separate jobs, and a model that is good at one is not automatically good at the other.
