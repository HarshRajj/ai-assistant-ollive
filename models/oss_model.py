"""
Open-Source model client — Qwen 2.5 via HuggingFace Serverless Inference API.

Uses ``huggingface_hub.InferenceClient`` for a clean, official API.

Provides:
  - ``query_oss_model(messages, placeholder)``
    Queries the model, writes the full response into a Streamlit placeholder
    after completion, and returns metrics.
  - ``query_oss_model_headless(messages)``
    Non-streaming variant for the evaluation pipeline (no placeholder).
"""

import time
from huggingface_hub import InferenceClient

from config import OSS_MODEL_ID, SYSTEM_PROMPT, HF_TOKEN, estimate_tokens


def _build_messages(messages: list[dict]) -> list[dict]:
    """Prepend the system prompt to a list of user/assistant messages."""
    return [{"role": "system", "content": SYSTEM_PROMPT}] + [
        {"role": m["role"], "content": m["content"]} for m in messages
    ]


def _get_client() -> InferenceClient:
    """Return an InferenceClient instance."""
    return InferenceClient(
        model=OSS_MODEL_ID,
        token=HF_TOKEN or None,
    )


def query_oss_model(
    messages: list[dict],
    placeholder=None,
) -> tuple[str, float, int]:
    """Query Qwen 2.5 and optionally display the result in a placeholder.

    Args:
        messages:    Conversation history.
        placeholder: Optional ``st.empty()`` container to write the response into.

    Returns:
        (full_text, latency_seconds, estimated_tokens)
    """
    hf_messages = _build_messages(messages)
    client = _get_client()

    t0 = time.perf_counter()
    if not HF_TOKEN:
        error_msg = "⚠️ HF_TOKEN not set in .env. Required for Qwen models."
        if placeholder is not None:
            placeholder.error(error_msg)
        return error_msg, 0.0, 0

    try:
        result = client.chat_completion(
            messages=hf_messages,
            max_tokens=512,
            temperature=0.7,
        )
        latency = time.perf_counter() - t0
        text = result.choices[0].message.content.strip() if result.choices else "(empty response)"

        if placeholder is not None:
            placeholder.markdown(text)

        return text, latency, estimate_tokens(text)

    except Exception as e:
        latency = time.perf_counter() - t0
        error_msg = f"⚠️ HF API error: {e}"
        if placeholder is not None:
            placeholder.error(error_msg)
        return error_msg, latency, 0


# Alias for evaluation pipeline (no placeholder needed)
def query_oss_model_headless(messages: list[dict]) -> tuple[str, float, int]:
    """Non-streaming query for the evaluation pipeline."""
    return query_oss_model(messages, placeholder=None)
