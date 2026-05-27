"""
Evaluation dashboard page — runs the automated evaluation suite and
renders interactive charts + detailed results table.
Includes: Cost+Latency table, Observability traces, Eval history, Human feedback.
"""

import json
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from evaluator import run_evaluation, CATEGORIES
from config import EVAL_LOG_PATH
from observability import load_traces, latency_percentiles, error_rate, guardrail_rate

# ---------------------------------------------------------------------------
# Cost + latency data (inline — deployment platform comparison)
# ---------------------------------------------------------------------------
COST_TABLE = [
    {"Model": "Qwen2.5-0.5B", "Platform": "HF Spaces (Free CPU)", "Type": "OSS",
     "Avg Latency (s)": "10–25", "Cost / 1K tokens": "$0.00", "Cost / Month @ 100K tok": "$0.00",
     "Notes": "Free tier; shared CPU; cold-start ~30s"},
    {"Model": "Qwen2.5-0.5B", "Platform": "HF Spaces (Pro GPU T4)", "Type": "OSS",
     "Avg Latency (s)": "1–3", "Cost / 1K tokens": "~$0.001", "Cost / Month @ 100K tok": "~$0.10",
     "Notes": "$9/mo HF Pro; T4 GPU"},
    {"Model": "Qwen2.5-0.5B", "Platform": "Modal (A10G)", "Type": "OSS",
     "Avg Latency (s)": "0.5–1.5", "Cost / 1K tokens": "~$0.0006", "Cost / Month @ 100K tok": "~$0.06",
     "Notes": "$0.000612/s; pay-per-use"},
    {"Model": "Qwen2.5-0.5B", "Platform": "RunPod (RTX 3090)", "Type": "OSS",
     "Avg Latency (s)": "0.3–1.0", "Cost / 1K tokens": "~$0.0004", "Cost / Month @ 100K tok": "~$0.04",
     "Notes": "$0.22/hr spot"},
    {"Model": "Qwen2.5-0.5B", "Platform": "Replicate", "Type": "OSS",
     "Avg Latency (s)": "1–4", "Cost / 1K tokens": "~$0.0015", "Cost / Month @ 100K tok": "~$0.15",
     "Notes": "$0.0002/sec; coldboot ~5s"},
    {"Model": "gpt-4o-mini", "Platform": "OpenAI API", "Type": "Frontier",
     "Avg Latency (s)": "1–3", "Cost / 1K tokens": "$0.00015 in / $0.0006 out",
     "Cost / Month @ 100K tok": "~$0.075", "Notes": "SLA 99.9%; per-token billing"},
]


def render_eval_page(openai_key: str) -> None:
    """Render the full evaluation dashboard page."""
    st.markdown("# 📊 Evaluation Dashboard")
    st.markdown(
        "Run the automated evaluation suite, explore observability traces, "
        "and review cost comparisons across deployment tiers."
    )
    st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)

    # Top-level tabs
    tab_eval, tab_cost, tab_obs, tab_feedback = st.tabs([
        "🧪 Evaluation",
        "💰 Cost + Latency",
        "🔭 Observability",
        "🗳️ Human Feedback",
    ])

    with tab_eval:
        _render_eval_tab(openai_key)

    with tab_cost:
        _render_cost_tab()

    with tab_obs:
        _render_observability_tab()

    with tab_feedback:
        _render_feedback_tab()
        # Guardrail log
        if st.session_state.get("guardrail_log"):
            st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="section-header">🛡️ Guardrail Events</div>',
                unsafe_allow_html=True,
            )
            gdf = pd.DataFrame(st.session_state.guardrail_log)
            st.dataframe(gdf, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Tab: Evaluation
# ---------------------------------------------------------------------------

def _render_eval_tab(openai_key: str) -> None:
    if "eval_results" not in st.session_state:
        st.session_state.eval_results = None

    if st.button("▶️ Run Full Evaluation", use_container_width=True, type="primary"):
        if not openai_key:
            st.error("⚠️ OpenAI API key required for LLM-as-Judge evaluation.")
        else:
            with st.spinner("Running evaluation suite — this may take a few minutes…"):
                results = run_evaluation(openai_key=openai_key)
                st.session_state.eval_results = results
                # Persist run to eval history
                if "eval_history" not in st.session_state:
                    st.session_state.eval_history = []
                st.session_state.eval_history.append({
                    "run_id": results[0]["eval_run_id"] if results else "?",
                    "results": results,
                })

    results = st.session_state.eval_results

    if results is not None:
        df = pd.DataFrame(results)
        _render_summary_metrics(df)
        st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)
        _render_category_chart(df)
        _render_latency_chart(df)
        _render_results_table(df)
    else:
        st.info("Click **▶️ Run Full Evaluation** to generate the comparison report.")

    # Eval history comparison
    if st.session_state.get("eval_history") and len(st.session_state.eval_history) > 1:
        st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-header">📈 Eval Run History</div>',
            unsafe_allow_html=True,
        )
        history_rows = []
        for run in st.session_state.eval_history:
            run_df = pd.DataFrame(run["results"])
            history_rows.append({
                "Run ID": run["run_id"],
                "Avg OSS Score": round(run_df["oss_score"].mean(), 2),
                "Avg Frontier Score": round(run_df["frontier_score"].mean(), 2),
                "Avg OSS Latency (s)": round(run_df["oss_latency"].mean(), 3),
                "Avg Frontier Latency (s)": round(run_df["frontier_latency"].mean(), 3),
            })
        st.dataframe(pd.DataFrame(history_rows), use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Tab: Cost + Latency
# ---------------------------------------------------------------------------

def _render_cost_tab() -> None:
    st.markdown('<div class="section-header">💰 Cost + Latency Comparison</div>', unsafe_allow_html=True)
    st.markdown(
        "Estimated pricing across deployment platforms for the OSS model "
        "(`Qwen2.5-0.5B-Instruct`) compared to the Frontier API tier. "
        "All figures are approximate as of May 2025."
    )

    cost_df = pd.DataFrame(COST_TABLE)

    # Color-code by type
    def highlight_type(row):
        if row["Type"] == "OSS":
            return ["background-color: #1a1a3a"] * len(row)
        return ["background-color: #2a1a3a"] * len(row)

    st.dataframe(
        cost_df.style.apply(highlight_type, axis=1),
        use_container_width=True,
        hide_index=True,
    )

    # Bar chart: latency comparison (using midpoints of ranges)
    st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-header">⚡ Latency by Platform</div>', unsafe_allow_html=True)

    latency_data = {
        "HF Spaces (Free CPU)": 17.5,
        "HF Spaces (Pro GPU T4)": 2.0,
        "Modal (A10G)": 1.0,
        "RunPod (RTX 3090)": 0.65,
        "Replicate": 2.5,
        "OpenAI GPT-4o-mini": 2.0,
    }
    fig = go.Figure(go.Bar(
        x=list(latency_data.keys()),
        y=list(latency_data.values()),
        marker=dict(
            color=["#667eea", "#764ba2", "#f093fb", "#4facfe", "#43e97b", "#fa709a"],
        ),
        text=[f"{v}s" for v in latency_data.values()],
        textposition="outside",
    ))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter"),
        yaxis=dict(title="Avg Latency (s)"),
        showlegend=False,
        margin=dict(t=20, b=60),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    > [!NOTE]
    > **This deployment** uses HF Spaces Free CPU for zero-cost public availability.
    > For production, Modal A10G offers the best cost-per-token with sub-second latency.
    """)


# ---------------------------------------------------------------------------
# Tab: Observability
# ---------------------------------------------------------------------------

def _render_observability_tab() -> None:
    st.markdown('<div class="section-header">🔭 Inference Traces</div>', unsafe_allow_html=True)

    df = load_traces()

    if df.empty:
        st.info("No traces recorded yet. Run the Arena or an Evaluation to generate traces.")
        return

    # Summary metrics
    c1, c2, c3, c4, c5 = st.columns(5)
    total = len(df)
    oss_p = latency_percentiles(df, "oss")
    fr_p = latency_percentiles(df, "frontier")
    err = error_rate(df, "oss")
    gr = guardrail_rate(df)

    c1.metric("Total Traces", total)
    c2.metric("OSS p50 / p90 Latency", f"{oss_p['p50']}s / {oss_p['p90']}s")
    c3.metric("Frontier p50 / p90", f"{fr_p['p50']}s / {fr_p['p90']}s")
    c4.metric("OSS Error Rate", f"{err:.1%}")
    c5.metric("Guardrail Rate", f"{gr:.1%}")

    st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)

    # Latency histogram
    st.markdown('<div class="section-header">Latency Distribution</div>', unsafe_allow_html=True)
    oss_df = df[df["model_type"] == "oss"]["latency_s"].dropna()
    fr_df = df[df["model_type"] == "frontier"]["latency_s"].dropna()

    fig = go.Figure()
    if not oss_df.empty:
        fig.add_trace(go.Histogram(
            x=oss_df, name="OSS", opacity=0.7,
            marker_color="#667eea", nbinsx=20,
        ))
    if not fr_df.empty:
        fig.add_trace(go.Histogram(
            x=fr_df, name="Frontier", opacity=0.7,
            marker_color="#764ba2", nbinsx=20,
        ))
    fig.update_layout(
        barmode="overlay",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter"),
        xaxis_title="Latency (s)",
        yaxis_title="Count",
        legend=dict(orientation="h", y=-0.2),
        margin=dict(t=10),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Tokens per second scatter
    st.markdown('<div class="section-header">Throughput (tokens/s) over time</div>', unsafe_allow_html=True)
    if "timestamp" in df.columns and "tokens_per_second" in df.columns:
        fig2 = px.scatter(
            df,
            x="timestamp",
            y="tokens_per_second",
            color="model_type",
            color_discrete_map={"oss": "#667eea", "frontier": "#764ba2"},
            template="plotly_dark",
            labels={"tokens_per_second": "Tokens/s", "timestamp": "Time", "model_type": "Model"},
        )
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter"),
            margin=dict(t=10),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Raw trace table
    st.markdown('<div class="section-header">Raw Trace Log</div>', unsafe_allow_html=True)
    display_cols = [c for c in [
        "timestamp", "model", "model_type", "latency_s", "tokens_out",
        "tokens_per_second", "guardrail_triggered", "guardrail_layer",
        "error", "category", "eval_run_id", "backend",
    ] if c in df.columns]
    st.dataframe(
        df[display_cols].sort_values("timestamp", ascending=False),
        use_container_width=True,
        hide_index=True,
    )

    if st.button("🗑️ Clear Trace Log", type="secondary"):
        from config import TRACES_LOG_PATH
        if TRACES_LOG_PATH.exists():
            TRACES_LOG_PATH.unlink()
        st.success("Trace log cleared.")
        st.rerun()


# ---------------------------------------------------------------------------
# Tab: Human Feedback
# ---------------------------------------------------------------------------

def _render_feedback_tab() -> None:
    st.markdown('<div class="section-header">🗳️ Human Feedback Log</div>', unsafe_allow_html=True)
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

            # Vote distribution pie chart
            if "vote" in log_df.columns:
                vote_counts = log_df["vote"].value_counts().reset_index()
                vote_counts.columns = ["Vote", "Count"]
                fig = px.pie(
                    vote_counts, values="Count", names="Vote",
                    color_discrete_sequence=["#667eea", "#764ba2", "#f093fb"],
                    template="plotly_dark",
                )
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter"),
                    margin=dict(t=10),
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.caption("No votes recorded yet.")
    else:
        st.caption("No votes recorded yet. Use the Arena to submit feedback.")


# ---------------------------------------------------------------------------
# Eval chart helpers
# ---------------------------------------------------------------------------

def _render_summary_metrics(df: pd.DataFrame) -> None:
    st.markdown('<div class="section-header">Summary Metrics</div>', unsafe_allow_html=True)
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
    st.markdown('<div class="section-header">Score by Category</div>', unsafe_allow_html=True)

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
    st.markdown('<div class="section-header">Latency per Prompt</div>', unsafe_allow_html=True)

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
    st.markdown('<div class="section-header">Detailed Results</div>', unsafe_allow_html=True)
    display_df = df[[
        "category", "prompt", "oss_score", "frontier_score",
        "oss_latency", "frontier_latency",
    ]].copy()
    display_df.columns = [
        "Category", "Prompt", "OSS Score", "Frontier Score",
        "OSS Latency (s)", "Frontier Latency (s)",
    ]
    st.dataframe(display_df, use_container_width=True, hide_index=True)
