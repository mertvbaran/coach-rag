# Chunking Strategy Comparison

How a document is split before embedding decides what the retriever can find. Three strategies are compared here on the same questions:

- **`whole_doc`** — treats each file as a single chunk.
- **`by_heading`** — splits on markdown `## ` headings.
- **`fixed_window`** — cuts every 300 words with no regard for structure. The floor of the comparison: it is here to show whether using structure buys anything at all.

Measured on 57 gold-standard questions (47 with an expected source, 10 deliberately out of scope). Questions and expected answers are in `eval/questions.yaml`.

## Results

Ordered best to worst by how often the correct source is ranked first. The best value in each column is in **bold**.

| chunker | pieces | correct source ranked 1st | found in top 5 | all sources in top 5 | of 5 shown, share correct | ranking quality |
|---|---|---|---|---|---|---|
| **by_heading** | 319 | **0.809** | 0.936 | **0.904** | **0.251** | **0.870** |
| whole_doc | 91 | 0.745 | **0.957** | 0.883 | 0.234 | 0.840 |
| fixed_window | 239 | 0.723 | 0.936 | 0.858 | 0.230 | 0.822 |

**What the columns mean.** All values run from 0 to 1, higher is better.

- **correct source ranked 1st** — how often the very first result was right. The strictest measure, and the one that matters most in practice: people read the top result. *(HitRate@1)*
- **found in top 5** — how often a correct source appeared anywhere in the five results shown. *(HitRate@5)*
- **all sources in top 5** — some questions have more than one correct source; this is the share of them that were found. *(Recall@5)*
- **of 5 shown, share correct** — necessarily low: most questions have only one or two correct sources, so three of the five slots can never be right. *(Precision@5)*
- **ranking quality** — a single number combining position and correctness. Rewards putting the right source *first*, not merely somewhere in the list. *(MRR)*

**Reading the table.** `by_heading` ranks the correct source first most often (0.809) and has the best ranking quality (0.870), which is why it is the strategy the system ships with. `whole_doc` edges ahead on finding a source anywhere in the top five (0.957): when a whole file is a single piece it is harder to miss the right document entirely, but harder to rank it top. Splitting on headings gives the search a unit that matches how a question is usually scoped — one section, one idea.

## Does returning more results help?

How often a correct source is found, as the number of results shown grows. A strategy that only catches up at ten results is finding the right document but burying it.

| chunker | in 1st | in top 3 | in top 5 | in top 10 |
|---|---|---|---|---|
| by_heading | **0.809** | 0.936 | 0.936 | 0.979 |
| whole_doc | 0.745 | 0.936 | 0.957 | 0.979 |
| fixed_window | 0.723 | 0.936 | 0.936 | 0.979 |

All three converge once ten results are shown, so the difference between them is about ordering, not about which documents they can reach at all.

## Rejecting questions the vault does not cover

A retriever always returns its closest matches, even for a question the corpus has nothing to say about. This checks whether a simple cutoff on the bi-encoder's similarity score is enough to catch those.

| chunker | out-of-scope | correctly rejected below 0.3 |
|---|---|---|
| whole_doc | 10 | 3/10 |
| by_heading | 10 | 3/10 |
| fixed_window | 10 | 3/10 |

It is not: no chunking strategy reliably separates in-scope from out-of-scope questions on similarity alone. This negative result is what led to the cross-encoder gate the system now uses. Two other reports follow it up — *Out-of-scope threshold analysis* shows why the raw similarity score fails, and *Threshold selection* shows how the replacement cutoff was fitted.
