"""
Arena page — split-screen benchmarking interface.

OpenAI streams token-by-token in the left column; Qwen renders its full
response in the right column after completion.  Latency, estimated tokens,
and a human feedback vote are displayed below.
"""

import json
import datetime
import streamlit as st

from guardrails import check_input_safety, check_output_safety
from models import stream_frontier_model, query_oss_model
from config import FRONTIER_MODEL_NAME, OSS_MODEL_ID, EVAL_LOG_PATH


def render_arena_page(openai_key: str) -> None:
    """Render the full arena page.

    Args:
        openai_key: Resolved OpenAI API key (sidebar → env fallback).
    """
    st.markdown("# 🏟️ Benchmarking Arena")
    st.markdown(
        "Enter a prompt to compare responses from **OpenAI** (streaming) and "
        "**Qwen 2.5** (full response) side-by-side."
    )
    st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)

    # ---- User input ----
    user_input = st.chat_input("Type your prompt…")

    if user_input:
        # ---- Input guardrail ----
        is_safe, reason = check_input_safety(user_input)
        if not is_safe:
            st.session_state.guardrail_log.append({
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "input": user_input,
                "reason": reason,
            })
            st.markdown(
                f'<div class="guardrail-alert">🛡️ <strong>{reason}</strong></div>',
                unsafe_allow_html=True,
            )
            st.stop()

        # ---- Display user prompt ----
        st.markdown(
            f'<div class="chat-bubble-user">{user_input}</div>'
            '<div style="clear:both"></div>',
            unsafe_allow_html=True,
        )

        st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)

        # ---- Split-screen columns ----
        col_frontier, col_oss = st.columns(2)

        with col_frontier:
            st.markdown(
                f'<div class="section-header">🔒 Frontier — {FRONTIER_MODEL_NAME}</div>',
                unsafe_allow_html=True,
            )
            frontier_placeholder = st.empty()

        with col_oss:
            st.markdown(
                f'<div class="section-header">🔓 OSS — {OSS_MODEL_ID.split("/")[-1]}</div>',
                unsafe_allow_html=True,
            )
            oss_placeholder = st.empty()

        # ---- Execute both models ----
        messages = [{"role": "user", "content": user_input}]

        # Frontier (streaming)
        with col_frontier:
            frontier_text, frontier_lat, frontier_tokens = stream_frontier_model(
                messages, openai_key, frontier_placeholder
            )

        # OSS (full response)
        with col_oss:
            oss_text, oss_lat, oss_tokens = query_oss_model(
                messages, oss_placeholder
            )

        # ---- Output guardrails ----
        fr_safe, fr_reason = check_output_safety(frontier_text)
        if not fr_safe:
            frontier_text = f"🛡️ [Filtered] {fr_reason}"
            frontier_placeholder.warning(frontier_text)
        oss_safe, oss_reason = check_output_safety(oss_text)
        if not oss_safe:
            oss_text = f"🛡️ [Filtered] {oss_reason}"
            oss_placeholder.warning(oss_text)

        # ---- Metrics row ----
        st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-header">📐 Execution Metrics</div>',
            unsafe_allow_html=True,
        )

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Frontier Latency", f"{frontier_lat:.3f}s")
        m2.metric("Frontier Est. Tokens", f"{frontier_tokens}")
        m3.metric("OSS Latency", f"{oss_lat:.3f}s")
        m4.metric("OSS Est. Tokens", f"{oss_tokens}")

        # ---- Human feedback vote ----
        st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-header">🗳️ Which response was better?</div>',
            unsafe_allow_html=True,
        )

        vote = st.radio(
            "Vote",
            options=[
                f"🟢 Frontier ({FRONTIER_MODEL_NAME})",
                f"🔵 OSS ({OSS_MODEL_ID.split('/')[-1]})",
                "🟡 Tie / Unsure",
            ],
            horizontal=True,
            label_visibility="collapsed",
        )

        if st.button("Submit Vote", use_container_width=True, type="primary"):
            record = {
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "prompt": user_input,
                "frontier_model": FRONTIER_MODEL_NAME,
                "oss_model": OSS_MODEL_ID,
                "frontier_response": frontier_text[:500],
                "oss_response": oss_text[:500],
                "frontier_latency": round(frontier_lat, 3),
                "oss_latency": round(oss_lat, 3),
                "frontier_tokens": frontier_tokens,
                "oss_tokens": oss_tokens,
                "vote": vote,
            }

            # Session state
            if "votes" not in st.session_state:
                st.session_state.votes = []
            st.session_state.votes.append(record)

            # Persist to JSONL
            with open(EVAL_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

            st.success("✅ Vote recorded!")

    else:
        # Show previous votes summary if any exist
        if "votes" in st.session_state and st.session_state.votes:
            st.markdown(
                '<div class="section-header">📋 Session Vote History</div>',
                unsafe_allow_html=True,
            )
            for i, v in enumerate(reversed(st.session_state.votes[-5:]), 1):
                st.caption(f"{i}. **{v['vote']}** — \"{v['prompt'][:60]}…\"")
