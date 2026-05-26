"""
Frontier model client — OpenAI GPT-4o-mini with streaming support.

Provides:
  - ``stream_frontier_model(messages, api_key, placeholder)``
    Streams tokens into a Streamlit placeholder in real time.
  - ``query_frontier_model(messages, api_key)``
    Non-streaming fallback for evaluation pipeline.
"""

import time
from openai import OpenAI

from config import FRONTIER_MODEL_NAME, SYSTEM_PROMPT, estimate_tokens


def _build_messages(messages: list[dict]) -> list[dict]:
    """Prepend the system prompt to a list of user/assistant messages."""
    return [{"role": "system", "content": SYSTEM_PROMPT}] + [
        {"role": m["role"], "content": m["content"]} for m in messages
    ]


def stream_frontier_model(
    messages: list[dict],
    api_key: str,
    placeholder,
) -> tuple[str, float, int]:
    """Stream GPT-4o-mini response token-by-token into a Streamlit placeholder.

    Args:
        messages:    Conversation history.
        api_key:     Resolved OpenAI API key.
        placeholder: A ``st.empty()`` container to write streaming chunks into.

    Returns:
        (full_text, latency_seconds, estimated_tokens)
    """
    if not api_key:
        placeholder.warning("⚠️ OpenAI API key not configured.")
        return "⚠️ OPENAI_API_KEY not set.", 0.0, 0

    client = OpenAI(api_key=api_key)
    oai_messages = _build_messages(messages)

    collected: list[str] = []
    t0 = time.perf_counter()

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
        return full_text, latency, estimate_tokens(full_text)

    except Exception as e:
        latency = time.perf_counter() - t0
        error_msg = f"⚠️ OpenAI error: {e}"
        placeholder.error(error_msg)
        return error_msg, latency, 0


def query_frontier_model(
    messages: list[dict],
    api_key: str,
) -> tuple[str, float, int]:
    """Non-streaming query for the evaluation pipeline.

    Returns:
        (full_text, latency_seconds, estimated_tokens)
    """
    if not api_key:
        return "⚠️ OPENAI_API_KEY not set.", 0.0, 0

    client = OpenAI(api_key=api_key)
    oai_messages = _build_messages(messages)

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
        return text, latency, estimate_tokens(text)
    except Exception as e:
        return f"⚠️ OpenAI error: {e}", time.perf_counter() - t0, 0
