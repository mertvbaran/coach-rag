"""Cross-encoder re-ranking and out-of-scope confidence gating.

Finding (see results/threshold_analysis.md): the bi-encoder's (embedder.py)
top-1 cosine score cannot reliably distinguish in-scope from out-of-scope
questions — "technical but different domain" questions (Kubernetes,
Blockchain) and coincidental vocabulary overlaps produce false positives.
A cross-encoder, which scores a question against a candidate chunk
directly instead of comparing two independent embeddings, separates the
two groups far better (AUROC and the coverage-risk curve are in
results/abstention_metrics.md).

Note (see results/rerank_impact.md): using this same cross-encoder to
RE-RANK results rather than just gate them was tested and rejected — it
systematically favors long, explanatory chunks over this vault's atomic
one-concept-per-page style and hurts HitRate@1 significantly. This module
is therefore used only for the in-scope/out-of-scope decision; ranking is
left to the bi-encoder.
"""

from pathlib import Path

import numpy as np

CROSS_ENCODER_MODEL = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"

# Derived by minimising a stated cost function rather than picked by eye
# (see experiments/calibrate_threshold.py, results/threshold_selection.md).
# Answering an out-of-scope question is weighted twice as costly as refusing
# an in-scope one, on the grounds that a user can rephrase a refusal but
# cannot tell that a confidently wrong answer is wrong.
#
# Earlier values, kept here because each correction is itself a finding:
# -5.5 was set to just clear the lowest in-scope score in a small sample --
# clean-looking on that sample, but it let through about a quarter of
# out-of-scope questions and could be flipped by rewording one
# (results/threshold_robustness.md). -3.94 was the cost-minimising fit over
# the first 57-question evaluation set (47 in-scope, 32 out-of-scope).
#
# This value folds in one correction recorded through the dashboard's
# feedback control (data/gate_feedback.jsonl) after a real out-of-scope
# question -- about Kafka -- scored inside the -3.94 boundary. Re-running
# experiments/calibrate_threshold.py against the evaluation set plus that
# correction (47 in-scope, 33 out-of-scope) moves the cost-minimising
# threshold to -3.68, with 5-fold cross-validation giving 3/33 false accepts
# and 5/47 false refuses on questions the threshold was not chosen from --
# see results/threshold_selection.md for the full fold-by-fold breakdown.
# This is the feedback loop working as designed: a real misclassification
# found in use tightens the boundary, rather than being a one-off patch.
#
# Note this is specific to the by_heading index: chunk length shifts the
# cross-encoder's score distribution, and applying this same cutoff to the
# whole_doc index wrongly refuses far more in-scope questions.
CE_OUT_OF_SCOPE_THRESHOLD = -3.68


class Reranker:
    def __init__(self, model_name: str = CROSS_ENCODER_MODEL):
        from sentence_transformers import CrossEncoder

        self.model = CrossEncoder(model_name)

    def score(self, question: str, texts: list[str]) -> list[float]:
        pairs = [(question, text[:512]) for text in texts]
        scores = self.model.predict(pairs)
        return [float(s) for s in scores]

    def rerank(self, question: str, texts: list[str], indices: list[int]) -> list[tuple[int, float]]:
        """Returns (original_index, cross_encoder_score) pairs sorted by score, descending."""
        ce_scores = self.score(question, texts)
        pairs = list(zip(indices, ce_scores))
        return sorted(pairs, key=lambda p: -p[1])

    def is_in_scope(self, question: str, texts: list[str], threshold: float = CE_OUT_OF_SCOPE_THRESHOLD) -> tuple[bool, float]:
        ce_scores = self.score(question, texts)
        top_score = max(ce_scores) if ce_scores else -999.0
        return top_score >= threshold, top_score
