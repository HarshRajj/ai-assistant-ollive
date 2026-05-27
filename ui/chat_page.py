"""
Arena page — split-screen benchmarking interface.

Features:
- OpenAI streams token-by-token (left column)
- Qwen renders full response (right column)
- Conversation memory (sliding window with summary)
- Tool use (calculator, web search, datetime)
- 3-layer guardrail checking with layer annotations
- Multi-turn conversation history per session
"""

import json
import datetime
import streamlit as st

from guardrails import check_input_safety, check_output_safety
from models import stream_frontier_model, query_oss_model
from config import FRONTIER_MODEL_NAME, OSS_MODEL_ID, EVAL_LOG_PATH
from memory import ConversationMemory
from tools import detect_and_run


def render_arena_page(openai_key: str) -> None:
    """Render the full arena page.

    Args:
        openai_key: Resolved OpenAI API key (sidebar → env fallback).
    """
    st.markdown("# 🏟️ Benchmarking Arena")
    st.markdown(
        "Enter a prompt to compare responses from **OpenAI** (streaming) and "
        "**Qwen 2.5** (full response) side-by-side. "
        "History is preserved per session with **conversation memory**."
    )
    st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)

    # ---- Memory + Tools controls (sidebar) ----
    _render_memory_controls()

    memory_enabled = st.session_state.get("memory_enabled", True)
    tools_enabled = st.session_state.get("tools_enabled", True)
    window_size = st.session_state.get("memory_window_size", 10)

    # Initialise per-model ConversationMemory objects
    if "frontier_memory" not in st.session_state:
        st.session_state.frontier_memory = ConversationMemory(window_size=window_size)
    if "oss_memory" not in st.session_state:
        st.session_state.oss_memory = ConversationMemory(window_size=window_size)

    frontier_mem: ConversationMemory = st.session_state.frontier_memory
    oss_mem: ConversationMemory = st.session_state.oss_memory

    # ---- User input ----
    user_input = st.chat_input("Type your prompt…")

    if user_input:
        # ---- Input guardrail (3-layer) ----
        guardrail_result = check_input_safety(
            user_input,
            openai_key=openai_key,
            run_llm_layer=False,  # LLM layer opt-in to save tokens
        )
        if not guardrail_result.safe:
            st.session_state.guardrail_log.append({
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "input": user_input,
                "layer": guardrail_result.layer,
                "reason": guardrail_result.reason,
                "latency_ms": guardrail_result.latency_ms,
            })
            st.error(
                f"🛡️ **[Layer: {guardrail_result.layer.upper()}]** "
                f"{guardrail_result.reason}"
            )
            st.stop()

        tool_name, tool_context = None, ""
        if tools_enabled:
            tool_name, tool_context = detect_and_run(user_input)

        # Add to message histories
        if memory_enabled:
            frontier_mem.add_user(user_input)
            oss_mem.add_user(user_input)
        else:
            st.session_state.frontier_messages.append({"role": "user", "content": user_input})
            st.session_state.oss_messages.append({"role": "user", "content": user_input})

        # Store tool annotation for display
        if "tool_annotations" not in st.session_state:
            st.session_state.tool_annotations = {}
        turn_key = str(frontier_mem.turn_count if memory_enabled else len(st.session_state.frontier_messages))
        if tool_name:
            st.session_state.tool_annotations[turn_key] = tool_name

    # ---- Render chat history ----
    if memory_enabled:
        all_messages = frontier_mem.get_context_messages()
        oss_all_messages = oss_mem.get_context_messages()
        n_msgs = len([m for m in all_messages if m["role"] != "system"])
    else:
        all_messages = st.session_state.frontier_messages
        oss_all_messages = st.session_state.oss_messages
        n_msgs = len(all_messages)

    # Filter out system messages for display
    display_messages = [m for m in all_messages if m["role"] != "system"]
    oss_display_messages = [m for m in oss_all_messages if m["role"] != "system"]

    for i in range(len(display_messages)):
        fm = display_messages[i]
        om = oss_display_messages[i] if i < len(oss_display_messages) else fm

        if fm["role"] == "user":
            # Tool annotation badge
            ann_key = str(i // 2 + 1)
            tool_ann = (st.session_state.get("tool_annotations") or {}).get(ann_key)
            tool_badge = f' <span style="background:#667eea22;border:1px solid #667eea;border-radius:4px;padding:1px 6px;font-size:0.75em">🔧 {tool_ann}</span>' if tool_ann else ""

            st.markdown(
                f'<div class="chat-bubble-user">{fm["content"]}{tool_badge}</div>'
                '<div style="clear:both"></div>',
                unsafe_allow_html=True,
            )
            st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)

            col_f, col_o = st.columns(2)
            with col_f:
                st.markdown(
                    f'<div class="section-header">🔒 Frontier — {FRONTIER_MODEL_NAME}</div>',
                    unsafe_allow_html=True,
                )
            with col_o:
                st.markdown(
                    f'<div class="section-header">🔓 OSS — {OSS_MODEL_ID.split("/")[-1]}</div>',
                    unsafe_allow_html=True,
                )

            # If this is the latest unanswered user message → generate response
            is_last_user = (i == len(display_messages) - 1)
            if is_last_user:
                with col_f:
                    f_ph = st.empty()
                with col_o:
                    o_ph = st.empty()

                # Build context: if tool_context, prepend to the latest message
                if tool_context and memory_enabled:
                    # Inject tool result as a system message for this turn only
                    f_ctx = frontier_mem.get_context_messages()
                    f_ctx[-1] = {"role": "user", "content": tool_context}
                    o_ctx = oss_mem.get_context_messages()
                    o_ctx[-1] = {"role": "user", "content": tool_context}
                elif tool_context:
                    f_ctx = [{"role": "user", "content": tool_context}]
                    o_ctx = [{"role": "user", "content": tool_context}]
                elif memory_enabled:
                    f_ctx = frontier_mem.get_context_messages()
                    o_ctx = oss_mem.get_context_messages()
                else:
                    f_ctx = st.session_state.frontier_messages
                    o_ctx = st.session_state.oss_messages

                with col_f:
                    f_text, f_lat, f_tok = stream_frontier_model(f_ctx, openai_key, f_ph)
                with col_o:
                    o_text, o_lat, o_tok = query_oss_model(o_ctx, o_ph)

                # Output guardrails
                f_out = check_output_safety(f_text)
                if not f_out.safe:
                    f_text = f"🛡️ [Filtered — {f_out.layer}] {f_out.reason}"
                    f_ph.warning(f_text)
                o_out = check_output_safety(o_text)
                if not o_out.safe:
                    o_text = f"🛡️ [Filtered — {o_out.layer}] {o_out.reason}"
                    o_ph.warning(o_text)

                # Save to memory
                if memory_enabled:
                    frontier_mem.add_assistant(f_text)
                    oss_mem.add_assistant(o_text)
                else:
                    st.session_state.frontier_messages.append({"role": "assistant", "content": f_text})
                    st.session_state.oss_messages.append({"role": "assistant", "content": o_text})

                # Metrics
                st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)
                st.markdown('<div class="section-header">📐 Execution Metrics</div>', unsafe_allow_html=True)
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Frontier Latency", f"{f_lat:.3f}s")
                m2.metric("Frontier Est. Tokens", f"{f_tok}")
                m3.metric("OSS Latency", f"{o_lat:.3f}s")
                m4.metric("OSS Est. Tokens", f"{o_tok}")

                _render_voting_widget(fm["content"], f_text, o_text, f_lat, o_lat, f_tok, o_tok)

        elif fm["role"] == "assistant":
            col_f, col_o = st.columns(2)
            with col_f:
                st.markdown(fm["content"])
            with col_o:
                st.markdown(om["content"])
            st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)

    if n_msgs == 0:
        if "votes" in st.session_state and st.session_state.votes:
            st.markdown(
                '<div class="section-header">📋 Session Vote History</div>',
                unsafe_allow_html=True,
            )
            for idx, v in enumerate(reversed(st.session_state.votes[-5:]), 1):
                st.caption(f"{idx}. **{v['vote']}** — \"{v['prompt'][:60]}…\"")


def _render_memory_controls() -> None:
    """Render memory and tools controls in the sidebar."""
    with st.sidebar:
        st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)
        st.markdown("**🧠 Memory & Tools**")

        memory_enabled = st.toggle("Conversation Memory", value=True, key="memory_enabled")
        if memory_enabled:
            st.slider("Window Size (turns)", 4, 20, 10, key="memory_window_size")

        tools_enabled = st.toggle("Tool Use", value=True, key="tools_enabled")
        if tools_enabled:
            st.caption("🔧 Calculator · 🔍 Web Search · 🕐 DateTime")

        if st.button("🗑️ Clear Memory", use_container_width=True):
            for key in ["frontier_memory", "oss_memory", "tool_annotations"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state.frontier_messages = []
            st.session_state.oss_messages = []
            st.rerun()


def _render_voting_widget(prompt, f_text, o_text, f_lat, o_lat, f_tok, o_tok):
    """Render the vote widget for the latest turn."""
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
            "prompt": prompt,
            "frontier_model": FRONTIER_MODEL_NAME,
            "oss_model": OSS_MODEL_ID,
            "frontier_response": f_text[:500],
            "oss_response": o_text[:500],
            "frontier_latency": round(f_lat, 3),
            "oss_latency": round(o_lat, 3),
            "frontier_tokens": f_tok,
            "oss_tokens": o_tok,
            "vote": vote,
        }
        if "votes" not in st.session_state:
            st.session_state.votes = []
        st.session_state.votes.append(record)

        with open(EVAL_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        st.success("✅ Vote recorded!")
