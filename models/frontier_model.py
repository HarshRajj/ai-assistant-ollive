"""
Frontier model client — OpenAI GPT-4o-mini with streaming + observability.

Provides:
  - ``stream_frontier_model(messages, api_key, placeholder, ...)``
    Streams tokens into a Streamlit placeholder in real time.
  - ``query_frontier_model(messages, api_key, ...)``
    Non-streaming fallback for evaluation pipeline.
"""

import time
from openai import OpenAI

from config import FRONTIER_MODEL_NAME, SYSTEM_PROMPT, estimate_tokens
from observability import make_trace, log_trace


def _build_messages(messages: list[dict]) -> list[dict]:
    """Prepend the system prompt to a list of user/assistant messages."""
    return [{"role": "system", "content": SYSTEM_PROMPT}] + [
        {"role": m["role"], "content": m["content"]} for m in messages
    ]


def stream_frontier_model(
    messages: list[dict],
    api_key: str,
    placeholder,
    eval_run_id: str = "",
    category: str = "",
) -> tuple[str, float, int]:
    """Stream GPT-4o-mini response token-by-token into a Streamlit placeholder.

    Args:
        messages:      Conversation history.
        api_key:       Resolved OpenAI API key.
        placeholder:   A ``st.empty()`` container to write streaming chunks into.
        eval_run_id:   ID for the current evaluation batch (for tracing).
        category:      Eval category label (for tracing).

    Returns:
        (full_text, latency_seconds, estimated_tokens)
    """
    if not api_key:
        placeholder.warning("⚠️ OpenAI API key not configured.")
        return "⚠️ OPENAI_API_KEY not set.", 0.0, 0

    client = OpenAI(api_key=api_key)
    oai_messages = _build_messages(messages)
    prompt_preview = messages[-1]["content"] if messages else ""

    collected: list[str] = []
    t0 = time.perf_counter()
    error = False
    error_msg = ""

    try:
        stream = client.chat.completions.create(
            model=FRONTIER_MODEL_NAME,
            messages=oai_messages,
            max_tokens=512,
            temperature=0.7,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                collected.append(delta.content)
                placeholder.markdown("".join(collected) + "▍")

        full_text = "".join(collected)
        latency = time.perf_counter() - t0
        placeholder.markdown(full_text)
        tokens = estimate_tokens(full_text)

    except Exception as e:
        latency = time.perf_counter() - t0
        full_text = f"⚠️ OpenAI error: {e}"
        tokens = 0
        error = True
        error_msg = str(e)
        placeholder.error(full_text)

    # Log observability trace
    trace = make_trace(
        model=FRONTIER_MODEL_NAME,
        model_type="frontier",
        prompt=prompt_preview,
        latency_s=latency,
        tokens_out=tokens,
        eval_run_id=eval_run_id,
        error=error,
        error_message=error_msg,
        category=category,
        backend="openai",
    )
    try:
        log_trace(trace)
    except Exception:
        pass

    return full_text, latency, tokens


def query_frontier_model(
    messages: list[dict],
    api_key: str,
    eval_run_id: str = "",
    category: str = "",
) -> tuple[str, float, int]:
    """Non-streaming query for the evaluation pipeline.

    Returns:
        (full_text, latency_seconds, estimated_tokens)
    """
    if not api_key:
        return "⚠️ OPENAI_API_KEY not set.", 0.0, 0

    prompt_preview = messages[-1]["content"] if messages else ""
    client = OpenAI(api_key=api_key)
    oai_messages = _build_messages(messages)
    error = False
    error_msg = ""

    t0 = time.perf_counter()
    try:
        response = client.chat.completions.create(
            model=FRONTIER_MODEL_NAME,
            messages=oai_messages,
            max_tokens=512,
            temperature=0.7,
        )
        latency = time.perf_counter() - t0
        text = response.choices[0].message.content.strip()
        tokens = estimate_tokens(text)
    except Exception as e:
        latency = time.perf_counter() - t0
        text = f"⚠️ OpenAI error: {e}"
        tokens = 0
        error = True
        error_msg = str(e)

    # Log observability trace
    trace = make_trace(
        model=FRONTIER_MODEL_NAME,
        model_type="frontier",
        prompt=prompt_preview,
        latency_s=latency,
        tokens_out=tokens,
        eval_run_id=eval_run_id,
        error=error,
        error_message=error_msg,
        category=category,
        backend="openai",
    )
    try:
        log_trace(trace)
    except Exception:
        pass

    return text, latency, tokens
