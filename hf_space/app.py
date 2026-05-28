"""
Ollive OSS Model — HuggingFace Space Entry Point
=================================================
Serves Qwen/Qwen2.5-0.5B-Instruct as a Gradio JSON API.

Endpoint: POST /run/predict
Input:  (messages: list[dict], max_tokens: int, temperature: float)
Output: dict with text, latency, tokens, model, guardrail_triggered
"""

import time
import json
import os

# Fix for "localhost is not accessible" error in some Docker environments
os.environ["NO_PROXY"] = "localhost,127.0.0.1,0.0.0.0"

import gradio as gr
from transformers import pipeline, AutoTokenizer

# ---------------------------------------------------------------------------
# Model loading (cached on module import — happens once at Space startup)
# ---------------------------------------------------------------------------

MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"

SYSTEM_PROMPT = (
    "You are a helpful, harmless, and honest AI personal assistant called Ollive. "
    "Answer user questions accurately and concisely. If you are unsure, say so. "
    "Never produce harmful, biased, or misleading content."
)

print(f"Loading {MODEL_ID}...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
pipe = pipeline(
    "text-generation",
    model=MODEL_ID,
    tokenizer=tokenizer,
    device_map="auto",          # CPU on free tier; GPU if available
    torch_dtype="auto",
)
print("Model loaded.")

# ---------------------------------------------------------------------------
# Safety guardrails (inline — no external deps)
# ---------------------------------------------------------------------------

BLOCKED_PATTERNS = [
    "ignore previous instructions",
    "bypass system",
    "ignore all previous instructions",
    "ignore your instructions",
    "you are now",
    "act as an unrestricted",
    "pretend you have no rules",
    "disregard your programming",
    "override your safety",
    "jailbreak",
    "do anything now",
    "developer mode",
    "sudo",
]

UNSAFE_OUTPUT_KEYWORDS = [
    "i'll help you hack",
    "here's how to make a bomb",
    "here is how to synthesize",
    "step-by-step instructions to harm",
    "here are instructions for illegal",
]

GUARDRAIL_ALERT = "[Safety Layer Triggered: Input Blocked due to Risk Pattern]"


def check_input_safety(text: str) -> tuple[bool, str]:
    lower = text.lower()
    for pattern in BLOCKED_PATTERNS:
        if pattern in lower:
            return False, f'{GUARDRAIL_ALERT} — matched: "{pattern}"'
    return True, ""


def check_output_safety(text: str) -> tuple[bool, str]:
    lower = text.lower()
    for kw in UNSAFE_OUTPUT_KEYWORDS:
        if kw in lower:
            return False, "Response was filtered by the output safety layer."
    return True, ""


# ---------------------------------------------------------------------------
# Inference
# ---------------------------------------------------------------------------

def estimate_tokens(text: str) -> int:
    return int(len(text.split()) * 1.33)


def predict(
    messages: list,
    max_tokens: int = 512,
    temperature: float = 0.7,
) -> dict:
    """Run inference on Qwen2.5-0.5B-Instruct.

    Args:
        messages:     OpenAI-format message list.
        max_tokens:   Maximum tokens to generate.
        temperature:  Sampling temperature.

    Returns:
        dict with keys: text, latency, tokens, model, guardrail_triggered.
    """
    # Flatten to single user text for input safety check
    user_text = " ".join(
        m.get("content", "") for m in messages if m.get("role") == "user"
    )

    # Layer 1: input safety
    is_safe, reason = check_input_safety(user_text)
    if not is_safe:
        return {
            "text": reason,
            "latency": 0.0,
            "tokens": 0,
            "model": MODEL_ID,
            "guardrail_triggered": True,
            "guardrail_reason": reason,
        }

    # Build chat messages with system prompt
    chat_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + [
        {"role": m["role"], "content": m["content"]} for m in messages
    ]

    # Format using tokenizer's chat template
    try:
        prompt = tokenizer.apply_chat_template(
            chat_messages,
            tokenize=False,
            add_generation_prompt=True,
        )
    except Exception:
        # Fallback: simple concatenation
        prompt = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in chat_messages
        ) + "\nASSISTANT:"

    t0 = time.perf_counter()
    try:
        output = pipe(
            prompt,
            max_new_tokens=max_tokens,
            temperature=temperature,
            do_sample=temperature > 0,
            pad_token_id=tokenizer.eos_token_id,
            return_full_text=False,
        )
        latency = time.perf_counter() - t0
        text = output[0]["generated_text"].strip()
    except Exception as e:
        latency = time.perf_counter() - t0
        return {
            "text": f"⚠️ Inference error: {e}",
            "latency": round(latency, 3),
            "tokens": 0,
            "model": MODEL_ID,
            "guardrail_triggered": False,
            "guardrail_reason": "",
        }

    # Layer 2: output safety
    out_safe, out_reason = check_output_safety(text)
    if not out_safe:
        return {
            "text": f"🛡️ [Filtered] {out_reason}",
            "latency": round(latency, 3),
            "tokens": estimate_tokens(text),
            "model": MODEL_ID,
            "guardrail_triggered": True,
            "guardrail_reason": out_reason,
        }

    return {
        "text": text,
        "latency": round(latency, 3),
        "tokens": estimate_tokens(text),
        "model": MODEL_ID,
        "guardrail_triggered": False,
        "guardrail_reason": "",
    }


# ---------------------------------------------------------------------------
# Gradio interface — JSON API + optional demo UI
# ---------------------------------------------------------------------------

def gradio_predict(messages_json: str, max_tokens: int, temperature: float) -> str:
    """Gradio-compatible wrapper. Accepts messages as JSON string."""
    try:
        messages = json.loads(messages_json)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON for messages."})
    result = predict(messages, max_tokens=max_tokens, temperature=temperature)
    return json.dumps(result, ensure_ascii=False)


with gr.Blocks(title="🫒 Ollive OSS Model API") as demo:
    gr.Markdown("# 🫒 Ollive OSS Model — `Qwen2.5-0.5B-Instruct`")
    gr.Markdown(
        "Public inference API for the [Ollive AI Benchmarking Arena](https://github.com/HarshRajj/ai-assistant-ollive). "
        "Send messages in OpenAI format and receive a JSON response.\n\n"
        "**API endpoint**: `POST /run/predict`"
    )

    with gr.Row():
        with gr.Column():
            messages_input = gr.Textbox(
                label="Messages (JSON array)",
                value='[{"role": "user", "content": "What is the capital of France?"}]',
                lines=4,
            )
            max_tokens_slider = gr.Slider(64, 1024, value=512, step=64, label="Max Tokens")
            temperature_slider = gr.Slider(0.0, 1.5, value=0.7, step=0.05, label="Temperature")
            run_btn = gr.Button("Run Inference", variant="primary")

        with gr.Column():
            output_box = gr.Textbox(label="Response (JSON)", lines=10)

    run_btn.click(
        gradio_predict,
        inputs=[messages_input, max_tokens_slider, temperature_slider],
        outputs=output_box,
    )

    gr.Markdown("""
    ## Request Format
    ```bash
    curl -X POST https://HarshRajj-ollive-oss.hf.space/run/predict \\
      -H "Content-Type: application/json" \\
      -d '{"data": ["[{\\"role\\":\\"user\\",\\"content\\":\\"Hello!\\"}]", 512, 0.7]}'
    ```
    """)


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", share = True)
