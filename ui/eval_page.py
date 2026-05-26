"""
Evaluation dashboard page — runs the automated evaluation suite and
renders interactive charts + detailed results table.
Also displays the human feedback log from eval_log.jsonl.
"""

import json
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from evaluator import run_evaluation, CATEGORIES
from config import EVAL_LOG_PATH


def render_eval_page(openai_key: str) -> None:
    """Render the full evaluation dashboard page.

    Args:
        openai_key: Resolved OpenAI API key.
    """
    st.markdown("# 📊 Evaluation Dashboard")
    st.markdown(
        "Run the automated evaluation suite to compare both assistants across "
        "**Hallucination**, **Content Safety**, and **Bias** dimensions."
    )
    st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)

    if "eval_results" not in st.session_state:
        st.session_state.eval_results = None

    if st.button("▶️ Run Full Evaluation", use_container_width=True, type="primary"):
        if not openai_key:
            st.error("⚠️ OpenAI API key required for LLM-as-Judge evaluation.")
        else:
            with st.spinner("Running evaluation suite — this may take a few minutes…"):
                results = run_evaluation(openai_key=openai_key)
                st.session_state.eval_results = results

    results = st.session_state.eval_results

    if results is not None:
        df = pd.DataFrame(results)
        _render_summary_metrics(df)
        st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)
        _render_category_chart(df)
        _render_latency_chart(df)
        _render_results_table(df)
    else:
        st.info("Click **Run Full Evaluation** to generate the comparison report.")

    # ---- Human feedback log ----
    st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)
    _render_feedback_log()

    # ---- Guardrail log ----
    if st.session_state.get("guardrail_log"):
        st.markdown(
            '<div class="section-header">🛡️ Guardrail Events</div>',
            unsafe_allow_html=True,
        )
        st.dataframe(
            pd.DataFrame(st.session_state.guardrail_log),
            use_container_width=True,
            hide_index=True,
        )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _render_feedback_log() -> None:
    """Show human feedback votes from eval_log.jsonl."""
    st.markdown(
        '<div class="section-header">🗳️ Human Feedback Log</div>',
        unsafe_allow_html=True,
    )
    if EVAL_LOG_PATH.exists():
        records = []
        with open(EVAL_LOG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        if records:
            log_df = pd.DataFrame(records)
            display_cols = [c for c in [
                "timestamp", "prompt", "vote",
                "frontier_latency", "oss_latency",
                "frontier_tokens", "oss_tokens",
            ] if c in log_df.columns]
            st.dataframe(log_df[display_cols], use_container_width=True, hide_index=True)
        else:
            st.caption("No votes recorded yet.")
    else:
        st.caption("No votes recorded yet. Use the Arena to submit feedback.")


def _render_summary_metrics(df: pd.DataFrame) -> None:
    st.markdown(
        '<div class="section-header">Summary Metrics</div>',
        unsafe_allow_html=True,
    )
    c1, c2, c3, c4 = st.columns(4)

    avg_oss_score = df["oss_score"].mean()
    avg_fr_score = df["frontier_score"].mean()
    avg_oss_lat = df["oss_latency"].mean()
    avg_fr_lat = df["frontier_latency"].mean()

    c1.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{avg_oss_score:.1f}</div>
        <div class="metric-label">Avg OSS Score (1-5)</div>
    </div>""", unsafe_allow_html=True)

    c2.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{avg_fr_score:.1f}</div>
        <div class="metric-label">Avg Frontier Score (1-5)</div>
    </div>""", unsafe_allow_html=True)

    c3.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{avg_oss_lat:.2f}s</div>
        <div class="metric-label">Avg OSS Latency</div>
    </div>""", unsafe_allow_html=True)

    c4.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{avg_fr_lat:.2f}s</div>
        <div class="metric-label">Avg Frontier Latency</div>
    </div>""", unsafe_allow_html=True)


def _render_category_chart(df: pd.DataFrame) -> None:
    st.markdown(
        '<div class="section-header">Score by Category</div>',
        unsafe_allow_html=True,
    )

    cat_df = df.groupby("category").agg(
        oss_mean=("oss_score", "mean"),
        frontier_mean=("frontier_score", "mean"),
    ).reindex(CATEGORIES)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="OSS (Qwen 2.5)",
        x=cat_df.index,
        y=cat_df["oss_mean"],
        marker_color="#667eea",
    ))
    fig.add_trace(go.Bar(
        name="Frontier (OpenAI)",
        x=cat_df.index,
        y=cat_df["frontier_mean"],
        marker_color="#764ba2",
    ))
    fig.update_layout(
        barmode="group",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter"),
        yaxis=dict(range=[0, 5.5], title="Score (1-5)"),
        legend=dict(orientation="h", y=-0.15),
        margin=dict(t=10),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_latency_chart(df: pd.DataFrame) -> None:
    st.markdown(
        '<div class="section-header">Latency per Prompt</div>',
        unsafe_allow_html=True,
    )

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(1, len(df) + 1)),
        y=df["oss_latency"],
        mode="lines+markers",
        name="OSS",
        line=dict(color="#667eea", width=2),
        marker=dict(size=6),
    ))
    fig.add_trace(go.Scatter(
        x=list(range(1, len(df) + 1)),
        y=df["frontier_latency"],
        mode="lines+markers",
        name="Frontier",
        line=dict(color="#764ba2", width=2),
        marker=dict(size=6),
    ))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter"),
        xaxis_title="Prompt #",
        yaxis_title="Latency (s)",
        legend=dict(orientation="h", y=-0.15),
        margin=dict(t=10),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_results_table(df: pd.DataFrame) -> None:
    st.markdown(
        '<div class="section-header">Detailed Results</div>',
        unsafe_allow_html=True,
    )
    display_df = df[[
        "category", "prompt", "oss_score", "frontier_score",
        "oss_latency", "frontier_latency",
    ]].copy()
    display_df.columns = [
        "Category", "Prompt", "OSS Score", "Frontier Score",
        "OSS Latency (s)", "Frontier Latency (s)",
    ]
    st.dataframe(display_df, use_container_width=True, hide_index=True)
