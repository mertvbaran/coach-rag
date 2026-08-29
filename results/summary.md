# Overview

A search tool over a personal knowledge base. Ask a question in plain language, get back the passages that answer it, each with its source. Everything runs on the machine it is installed on — no text is sent anywhere.

## How it works

Ordinary search matches words. This matches meaning: every passage in the notes is converted into a list of numbers that stands for what it says, the question is converted the same way, and the closest passages come back. A question phrased differently from the notes still finds them.

The collection is 91 files, cut into 319 passages at their section headings.

## How well it works

Measured on 57 questions written against the notes: 47 with a known correct source, 10 deliberately about topics the notes never cover.

| | result |
|---|---|
| correct source ranked first | **81%** of questions |
| same, without using document structure | 72% |
| telling covered from uncovered questions apart | **0.979** out of 1.0 |

Splitting documents at their headings rather than by word count is what accounts for most of the difference between the first two rows — the same notes, cut differently.

## Knowing when not to answer

A search will always return its closest match, even for a question the notes have nothing to do with. So before answering, the system checks whether the question is covered at all, and says so when it is not.

Getting that check right took three attempts. A simple similarity cutoff did not work — questions from other technical fields score just as high as real ones. A second model that reads the question and passage together did work, but only for this decision: using it to re-order results made them worse. And the cutoff itself, first picked by eye, turned out to flip its decision when a question was reworded; it is now fitted from data at -3.68 and checked against questions it was not fitted on.

## What did not work

Three ideas were tried, measured, and dropped. They are kept in the reports because a measured failure is worth more than an untested assumption.

- **Combining meaning-based and keyword search.** Standard advice, but it made results worse at every mix tested. These notes all share the same vocabulary, so keyword matching separates almost nothing.
- **Re-ordering results with a second model.** Dropped rank-1 accuracy sharply. That model prefers long, explanatory passages, while these notes are deliberately short and focused.
- **Tuning a rule until it scored perfectly.** It did — on the very questions used to tune it, then failed on questions held back. A reminder of why the honest number is the one measured on data the choice was not made from.

## Where to look next

The other reports on this tab go into each of these:

- **How should text be split?** — the comparison behind the numbers above.
- **Where the search gets it wrong** — the questions it ranks worst, and the two patterns behind them.
- **Hybrid search** and **Re-ranking** — the two rejected ideas, with their measurements.
- **Why a simple cutoff was not enough**, **How the threshold was chosen**, **Is the threshold robust to rephrasing?**, and **Measuring the coverage check** — the full story of the refuse-or-answer decision.
