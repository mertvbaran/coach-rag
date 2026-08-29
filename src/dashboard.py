"""Streamlit dashboard: a thin presentation layer over the existing pipeline.

No retrieval logic lives here. "Ask" reuses search() and Reranker exactly as
query.py does; "Results" reads the markdown tables already written by the
scripts under experiments/. This file only exists to make the same pipeline
easier to demo and to browse the findings without opening several files.

The interface is bilingual because the vault it searches is Turkish while
the code and reports are English -- a reader of either language should be
able to use it.

Run with: streamlit run src/dashboard.py
"""

import html
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from chunkers import readable_text
from config import CACHE_DIR, DATA_DIR, INDEX_DIR, RESULTS_DIR, TOP_K
from embedder import Embedder
from feedback import record as record_feedback
from feedback import summary as feedback_summary
from reranker import CE_OUT_OF_SCOPE_THRESHOLD, Reranker
from store import load_index, search

st.set_page_config(page_title="Recall", page_icon="◧", layout="centered")

# Ends of the band the score bars are drawn across, measured over the top 5
# results for all 57 evaluation questions against the by_heading index:
# min 0.230, 5th percentile 0.285, 95th 0.758, max 0.829. Drawn against 0-1
# every bar would sit at the same half-full mark and show nothing.
#
# The bars for one query often land close together. That is the real shape of
# the data -- the top hits are usually different sections of the same note --
# and the scale is deliberately absolute, so a weak set of results looks weak
# instead of being stretched to fill the bar.
SCORE_FLOOR = 0.25
SCORE_CEIL = 0.83

# unsafe_allow_html bypasses HTML sanitization entirely (unlike st.html, which
# runs everything through DOMPurify and drops bare <style> tags). style.css
# carries its own @import for the faces, each behind a real fallback stack.
st.markdown(
    f"<style>{(Path(__file__).parent / 'style.css').read_text(encoding='utf-8')}</style>",
    unsafe_allow_html=True,
)

TEXT = {
    "en": {
        "tagline": "Ask your personal knowledge base a question, get back the passages that answer it, each with its source.",
        "tagline_stats": "How the search works, and how well it was measured to work.",
        "privacy": "Runs entirely on this machine. Nothing is sent anywhere.",
        "stats_link": "How does this work? →",
        "back_to_ask": "← Back",
        "question_label": "Question",
        "placeholder": "Why is the ROC curve threshold-independent?",
        "search": "Search",
        "sources_label": "Passages to return",
        "gate_label": "Say so when a question is not covered",
        "gate_help": (
            "Checks whether the knowledge base covers the question before answering, "
            "and says so when it does not. Turn this off to always see the closest "
            "matches."
        ),
        "no_index": "No `{chunker}` index found. Run `python src/build_index.py --chunker {chunker}` first.",
        "retrieving": "Searching",
        "first_search": "Loading the models for the first search.",
        "not_covered_lede": "Not covered.",
        "not_covered": "The knowledge base has nothing on this. The closest passages are below.",
        "asked": "Showing results for <em>{question}</em>",
        "stale": "Press Enter to search. Results below still belong to <em>{question}</em>",
        "try": "Try one of these",
        # Matched to data/sample/, not to any particular vault, so a repo clone
        # with no notes of its own still gets three questions the sample data
        # answers. Each wording was also checked directly against the gate
        # (see reranker.is_in_scope): a coverage question's cross-encoder
        # score varies with phrasing (threshold_robustness.md), so a wording
        # that happens to sit close to the cutoff would make the very first
        # thing a new user tries look broken. "Why does gradient descent
        # sometimes fail to converge?" scored -4.70 in Turkish translation --
        # below the -3.94 cutoff -- while "How does gradient descent work?"
        # scores +1.49/+1.47 in both languages, comfortably clear of it.
        "examples": [
            "How does gradient descent work?",
            "What is overfitting and how do you detect it?",
            "Why use cross validation instead of a single train/test split?",
        ],
        "wrong_refuse": "This should have been answered",
        "wrong_accept": "This should have been refused",
        "feedback_help_with_score": (
            "Report that the coverage decision was wrong. Corrections are stored "
            "locally and used the next time the threshold is fitted.\n\n"
            "Gate's raw score: {score:.2f} (cutoff: {threshold})"
        ),
        "recorded": "Recorded. {summary}",
        "stored_in": "Written to `{name}`, stays on this machine.",
        "report_label": "Report",
        "not_generated": "`{name}` not generated yet. Run the corresponding script in `experiments/`.",
        "english_only": "This report has no Turkish version yet, so the English one is shown.",
        "reports": {
            "Overview": "summary.md",
            "How should text be split? — chunking comparison": "chunking.md",
            "Where the search gets it wrong": "disagreement_analysis.md",
            "Hybrid search: tested and rejected": "hybrid_impact.md",
            "Re-ranking: tested and rejected": "rerank_impact.md",
            "Measuring the coverage check": "abstention_metrics.md",
            "How the threshold was chosen": "threshold_selection.md",
            "Is the threshold robust to rephrasing?": "threshold_robustness.md",
            "Why a simple cutoff was not enough": "threshold_analysis.md",
        },
    },
    "tr": {
        "tagline": "Kişisel bilgi tabanınıza soru sorun, cevabı içeren bölümleri kaynağıyla birlikte alın.",
        "tagline_stats": "Arama nasıl çalışıyor ve ne kadar iyi çalıştığı nasıl ölçüldü.",
        "privacy": "Tamamen bu cihazda çalışır. Hiçbir veri dışarı gönderilmez.",
        "stats_link": "Nasıl çalışır? →",
        "back_to_ask": "← Geri",
        "question_label": "Soru",
        "placeholder": "ROC eğrisi neden eşikten bağımsız bir metrik?",
        "search": "Ara",
        "sources_label": "Getirilecek bölüm sayısı",
        "gate_label": "Kapsam dışındaki soruları söyle",
        "gate_help": (
            "Cevap vermeden önce sorunun bilgi tabanında karşılığı var mı diye bakar, "
            "yoksa bunu söyler. Kapatırsanız her soru için en yakın sonuçları "
            "gösterir."
        ),
        "no_index": "`{chunker}` indeksi bulunamadı. Önce `python src/build_index.py --chunker {chunker}` çalıştırın.",
        "retrieving": "Aranıyor",
        "first_search": "İlk arama için modeller yükleniyor.",
        "not_covered_lede": "Bu konu işlenmemiş.",
        "not_covered": "Bilgi tabanında bu konuda bir şey yok. En yakın bölümler aşağıda.",
        "asked": "<em>{question}</em> için sonuçlar",
        "stale": "Aramak için Enter'a basın. Aşağıdaki sonuçlar hâlâ <em>{question}</em> sorusuna ait",
        "try": "Şunlardan birini deneyin",
        "examples": [
            "Gradient descent nasıl çalışır?",
            "Overfitting nedir, nasıl fark edilir?",
            "Tek bir train/test bölmesi yerine neden cross validation kullanılır?",
        ],
        "wrong_refuse": "Bu soruya cevap verilmeliydi",
        "wrong_accept": "Bu soru reddedilmeliydi",
        "feedback_help_with_score": (
            "Kapsam kararının yanlış olduğunu bildirin. Bildirimler bu cihazda "
            "saklanır ve eşik bir sonraki kalibrasyonda bu verilerle yeniden "
            "hesaplanır.\n\n"
            "Denetimin ham skoru: {score:.2f} (eşik: {threshold})"
        ),
        "recorded": "Kaydedildi. {summary}",
        "stored_in": "`{name}` dosyasına yazıldı, bu cihazda kalır.",
        "report_label": "Rapor",
        "not_generated": "`{name}` henüz üretilmemiş. `experiments/` altındaki ilgili scripti çalıştırın.",
        "english_only": "Bu raporun Türkçe sürümü henüz yok, İngilizcesi gösteriliyor.",
        "reports": {
            "Genel bakış": "summary.md",
            "Metni nasıl bölmeli? — chunking karşılaştırması": "chunking.md",
            "Aramanın yanıldığı yerler": "disagreement_analysis.md",
            "Hibrit arama: denendi ve reddedildi": "hybrid_impact.md",
            "Yeniden sıralama: denendi ve reddedildi": "rerank_impact.md",
            "Kapsam denetiminin ölçümü": "abstention_metrics.md",
            "Eşik nasıl belirlendi": "threshold_selection.md",
            "Eşik farklı ifadelere dayanıklı mı?": "threshold_robustness.md",
            "Basit eşik neden yetmedi": "threshold_analysis.md",
        },
    },
}


# show_spinner=False on all three: Streamlit's default spinner announces the
# function name ("Running get_reranker()"), which leaks an implementation
# detail into the interface. The caller shows one spinner of its own instead.
@st.cache_resource(show_spinner=False)
def get_embedder():
    return Embedder(CACHE_DIR)


@st.cache_resource(show_spinner=False)
def get_reranker():
    return Reranker()


@st.cache_data(show_spinner=False)
def get_index(chunker: str):
    return load_index(INDEX_DIR, chunker)


def render_ask_tab(t: dict):
    # The index is fixed rather than selectable. by_heading wins on rank-1
    # accuracy and MRR (see the Measurements tab), and the confidence gate's
    # threshold is calibrated against its score distribution specifically --
    # on whole_doc the same threshold wrongly refuses 5 of 47 in-scope
    # questions instead of 2. Offering the other indexes here would let a
    # viewer silently pick a worse-performing, miscalibrated configuration.
    chunker = "by_heading"
    if not (INDEX_DIR / f"{chunker}.npy").exists():
        st.warning(t["no_index"].format(chunker=chunker))
        return

    # A form submits on Enter as well as on the button, so a question can be
    # asked without reaching for the mouse.
    with st.form("ask", clear_on_submit=False):
        typed = st.text_input(
            t["question_label"],
            key="question_box",
            placeholder=t["placeholder"],
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button(t["search"], type="primary")
        with st.expander(t["sources_label"], expanded=False):
            k = st.slider(t["sources_label"], min_value=1, max_value=10, value=TOP_K,
                          label_visibility="collapsed")
            scope_check = st.checkbox(t["gate_label"], value=True, help=t["gate_help"])

    # Keep the last result across reruns, so clicking the feedback button
    # below does not wipe the answer off the screen.
    if submitted and typed:
        st.session_state["last_query"] = (typed, k, scope_check)

    # An empty page says nothing about what the tool can be asked. Three real
    # questions from the notes do, and double as a starting point.
    if "last_query" not in st.session_state:
        examples = "".join(f"<em>{html.escape(q)}</em>" for q in t["examples"])
        st.html(f'<div class="tryline"><span class="lbl">{t["try"]}</span>{examples}</div>')
        return

    question, k, scope_check = st.session_state["last_query"]

    # The box can hold a question that has not been submitted yet, while the
    # results below still belong to the previous one. Say so plainly instead of
    # letting stale results sit under a new question and look like its answer.
    stale = bool(typed.strip()) and typed.strip() != question.strip()

    # The first search of a session loads the models into memory and takes
    # several seconds; later ones are fast. Saying so avoids the impression
    # that the system is simply slow.
    first_run = "warmed_up" not in st.session_state
    in_scope, ce_score = None, None
    with st.spinner(t["first_search"] if first_run else t["retrieving"]):
        chunks, embeddings = get_index(chunker)
        embedder = get_embedder()
        query_vec = embedder.embed([question])[0]
        results = search(query_vec, embeddings, k=k)

        if scope_check:
            pool = search(query_vec, embeddings, k=10)
            pool_texts = [chunks[idx]["text"] for idx, _ in pool]
            reranker = get_reranker()
            in_scope, ce_score = reranker.is_in_scope(question, pool_texts)
    st.session_state["warmed_up"] = True

    # Built as one block of own-class HTML rather than as a series of Streamlit
    # containers: the results have to sit flush against a single margin rule
    # with their ranks inside it, and each st.html call would otherwise land in
    # a separate container with Streamlit's own spacing between them. It also
    # avoids depending on Streamlit's generated class names, which change per
    # release and would break silently on upgrade.
    parts = []
    if stale:
        parts.append(f'<div class="asked">{t["stale"].format(question=html.escape(question))}</div>')
    else:
        # The refusal is the one place the accent colour appears. It states the
        # outcome in plain words; the score behind it belongs with the report
        # control below, not in the sentence a reader has to parse first.
        if scope_check and not in_scope:
            parts.append(
                f'<div class="refusal"><span class="lede">{t["not_covered_lede"]}</span> '
                f'{t["not_covered"]}</div>'
            )
        parts.append(f'<div class="asked">{t["asked"].format(question=html.escape(question))}</div>')

    for rank, (idx, score) in enumerate(results, start=1):
        chunk = chunks[idx]
        preview = html.escape(readable_text(chunk, 300))

        # The bar is scaled across the band these scores actually occupy
        # rather than 0-1: cosine similarities here sit between roughly 0.35
        # and 0.75, so a bar drawn against the full range would leave every
        # result looking identically half-full and show nothing.
        filled = max(0.0, min(1.0, (score - SCORE_FLOOR) / (SCORE_CEIL - SCORE_FLOOR)))
        parts.append(
            f'<div class="hit{" stale" if stale else ""}">'
            f'<span class="rank">{rank:02d}</span>'
            f'<span class="score"><span class="bar"><i style="width:{filled:.0%}"></i></span>'
            f'{score:.3f}</span>'
            f'<div class="path">{html.escape(chunk["doc_path"])}</div>'
            f'<div class="text">{preview}…</div>'
            f"</div>"
        )
    st.html("".join(parts))

    # Placed after the results, not before them: it is a comment on what was
    # returned, and putting it above made it read like a control for the search.
    #
    # The threshold is fitted on a hand-written question set, which is only a
    # guess at what gets asked. Corrections recorded here go into
    # data/gate_feedback.jsonl so recalibration can use questions that were
    # actually asked -- see src/feedback.py and experiments/calibrate_threshold.py.
    #
    # The gate's raw cross-encoder score used to sit next to this button as
    # plain text ("confidence -3.68 against a threshold of -3.68") -- an
    # unexplained negative logit next to an unrelated cutoff, on every single
    # result. It is real information for someone deciding whether to file a
    # correction, so it moves into the button's tooltip instead of the
    # default view a first-time reader sees.
    if scope_check and in_scope is not None and not stale:
        label = t["wrong_refuse"] if not in_scope else t["wrong_accept"]
        help_text = t["feedback_help_with_score"].format(score=ce_score, threshold=CE_OUT_OF_SCOPE_THRESHOLD)
        clicked = st.button(label, key=f"fb_{hash(question)}", help=help_text)
        if clicked:
            path = record_feedback(DATA_DIR, question, ce_score, CE_OUT_OF_SCOPE_THRESHOLD, in_scope, chunker)
            st.success(t["recorded"].format(summary=feedback_summary(DATA_DIR)))
            st.caption(t["stored_in"].format(name=path.name))


def render_results_tab(t: dict, lang: str):
    reports = t["reports"]
    label = st.selectbox(t["report_label"], list(reports.keys()), label_visibility="collapsed")

    # Reports are written once per language: name.md and name.tr.md. Fall back
    # to English if a translation has not been generated yet, rather than
    # showing nothing.
    stem = reports[label].removesuffix(".md")
    path = RESULTS_DIR / f"{stem}.tr.md" if lang == "tr" else RESULTS_DIR / f"{stem}.md"
    if not path.exists():
        path = RESULTS_DIR / f"{stem}.md"
        if path.exists():
            st.caption(f":gray[{t['english_only']}]")
    if not path.exists():
        st.info(t["not_generated"].format(name=path.name))
        return

    # A keyed container carries a real class (st-key-report), which is the
    # supported way to scope CSS to one part of the page. The report's own
    # heading scale then applies without touching the rest of the interface.
    with st.container(key="report"):
        st.markdown(path.read_text(encoding="utf-8"))


# Asking a question is the product; the measurements are a secondary door for
# anyone curious enough to open it, so it is a quiet button styled as a link
# rather than a tab bar competing with the search box for the page's top
# position. The language selector is a control, not content, so it sits
# beside the wordmark rather than inside it.
if "showing_stats" not in st.session_state:
    st.session_state["showing_stats"] = False

# The language needs to be known before the labels below are picked, but the
# selectbox itself has to render in its column further down -- so read the
# widget's last known value from session state (Streamlit keeps it there
# under its auto-generated key on every rerun) and fall back to English only
# on the very first load.
_lang_key = "lang_select"
lang_prior = st.session_state.get(_lang_key, "English")
t = TEXT["tr" if lang_prior == "Türkçe" else "en"]

def _toggle_stats():
    st.session_state["showing_stats"] = not st.session_state["showing_stats"]


name_col, stats_col, lang_col = st.columns([3.6, 1.1, 1], vertical_alignment="bottom")
with name_col:
    st.html('<div class="masthead"><span class="name">Recall</span></div>')
with stats_col:
    label = t["back_to_ask"] if st.session_state["showing_stats"] else t["stats_link"]
    # A callback rather than reading the button's return value: the return
    # value flips the label to what it should become right as the script that
    # draws this same button is still running with the label read moments
    # earlier, so the button appears to need two clicks. on_click runs before
    # the rerun that draws the label, so the label shown is always correct.
    st.button(label, key="stats_link", on_click=_toggle_stats)
with lang_col:
    lang = st.selectbox("Language / Dil", ["English", "Türkçe"], label_visibility="collapsed", key=_lang_key)
is_tr = lang == "Türkçe"
t = TEXT["tr" if is_tr else "en"]

st.caption(t["tagline_stats"] if st.session_state["showing_stats"] else t["tagline"])

if st.session_state["showing_stats"]:
    render_results_tab(t, "tr" if is_tr else "en")
else:
    render_ask_tab(t)

st.html(f'<div class="colophon"><span>{t["privacy"]}</span></div>')
