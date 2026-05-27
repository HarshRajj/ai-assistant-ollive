# 🫒 Ollive AI Benchmarking Arena

A production-grade LLM benchmarking playground comparing **OpenAI GPT-4o-mini** (Frontier) against **Qwen 2.5** (Open Source) in a split-screen arena with streaming, 3-layer safety guardrails, conversation memory, tool use, structured observability, and an automated evaluation PDF.

[![HF Space](https://img.shields.io/badge/🤗%20HF%20Space-OSS%20Model-blue)](https://HarshRajj-ollive-oss.hf.space)
[![Streamlit App](https://img.shields.io/badge/Streamlit-Demo-red)](https://HarshRajj-ollive-arena.hf.space)

---

## Quick Start

```bash
# 1. Clone & enter the project
git clone https://github.com/HarshRajj/ai-assistant-ollive && cd ai-assistant-ollive

# 2. Copy environment template and fill in your keys
cp .env.example .env
#    → Set OPENAI_API_KEY (required for Frontier tier + LLM judge)
#    → HF_TOKEN is optional (only needed for hf_inference fallback)

# 3. Install dependencies (requires uv: https://docs.astral.sh/uv/)
uv sync

# 4. Launch the app
uv run streamlit run app.py
```

The app opens at **http://localhost:8501**.

> **No API keys?** You can also enter your OpenAI key at runtime via the sidebar password field — stored in volatile session memory only, never written to disk.

---

## Architecture

```
ai-assistant-ollive/
├── app.py                   ← Streamlit entry point, sidebar, page routing
├── config.py                ← Centralized env vars, model IDs, COST_TABLE
├── guardrails.py            ← 3-layer safety pipeline (pattern→semantic→LLM)
├── memory.py                ← ConversationMemory (sliding window + summarization)
├── observability.py         ← InferenceTrace dataclass, JSONL logging, analytics
├── tool_dispatcher.py       ← Intent detection → tool dispatch
├── generate_eval_report.py  ← Headless eval → PDF via reportlab
│
├── models/
│   ├── frontier_model.py    ← GPT-4o-mini with SSE streaming + observability
│   └── oss_model.py         ← Qwen 2.5 via HF Space API (+ HF Inference fallback)
│
├── tools/
│   ├── calculator.py        ← Safe arithmetic eval (no eval())
│   ├── web_search.py        ← DuckDuckGo Instant Answer (no API key)
│   └── datetime_tool.py     ← Current date/time info
│
├── evaluator/
│   ├── dataset.py           ← 18 curated test prompts
│   ├── judge.py             ← LLM-as-Judge (GPT-4o-mini, 1-5 scale)
│   └── runner.py            ← Eval orchestrator with eval_run_id tracking
│
├── hf_space/
│   ├── app.py               ← Gradio JSON API server for Qwen2.5-0.5B-Instruct
│   ├── requirements.txt     ← Space dependencies
│   └── README.md            ← HF Space metadata + API docs
│
├── ui/
│   ├── styles.py            ← Premium CSS (glassmorphism, animations)
│   ├── chat_page.py         ← Arena: split-screen + memory + tools + guardrails
│   └── eval_page.py         ← 4-tab dashboard (Eval / Cost / Observability / Feedback)
│
├── .env.example             ← Template for API keys
├── pyproject.toml           ← uv project manifest
├── eval_log.jsonl           ← Human feedback votes (auto-generated, gitignored)
└── traces.jsonl             ← Observability traces (auto-generated, gitignored)
```

---

## Features

### 🏟️ Arena (Split-Screen Benchmarking)
- OpenAI streams token-by-token (left column)
- Qwen 2.5 renders full response (right column)
- `st.metric` widgets: Latency and Est. Tokens per model
- Human feedback vote persists to `eval_log.jsonl`

### 🧠 Conversation Memory
- **Sliding window** strategy — last N turns kept in full (configurable 4–20 turns)
- **Auto-summarization** — older turns compressed via GPT-4o-mini when buffer exceeds threshold; falls back to extractive heuristic if no API key
- Toggle and window-size slider in sidebar; per-model independent memory

### 🔧 Tool Use
| Tool | Trigger | Backend |
|------|---------|---------|
| Calculator | Math expressions, "what is X × Y" | Safe `compile()` — no `eval()` |
| Web Search | "search for", "latest news", "look up" | DuckDuckGo Instant Answer API (free) |
| DateTime | "what time is it", "today's date" | `datetime` stdlib |

Tool results are injected into the model context before generation. Tool call annotations appear as inline badges in the chat.

### 🛡️ Safety Guardrails (3-Layer)
| Layer | Method | Latency |
|-------|--------|---------|
| 1 — Pattern | Keyword/regex block list (28 patterns) | < 1ms |
| 2 — Semantic | TF-IDF cosine similarity vs harmful intent corpus | ~5ms |
| 3 — LLM Judge | GPT-4o-mini binary safety classifier (opt-in) | ~500ms |

Returns a `GuardrailResult` dataclass with `layer`, `reason`, and `latency_ms`. All events logged to the dashboard.

### 📊 Evaluation Dashboard (4 tabs)

**Evaluation** — LLM-as-Judge scoring across 18 prompts (Hallucination Rate / Content Safety / Bias). Eval run history comparison.

**Cost + Latency** — Interactive bar chart + table comparing 6 deployment tiers:
- HF Spaces Free CPU, HF Spaces Pro GPU, Modal A10G, RunPod RTX 3090, Replicate, OpenAI API

**Observability** — Inference trace viewer with:
- p50, p90, p99 latency percentiles per model
- Error rate and guardrail rate metrics
- Latency histogram and tokens/s scatter plot over time

**Human Feedback** — Vote distribution pie chart + session log

### 🚀 OSS Model Deployment

The OSS model is deployed as a **HuggingFace Space** at:
`https://HarshRajj-ollive-oss.hf.space`

**API Usage:**
```bash
curl -X POST https://HarshRajj-ollive-oss.hf.space/run/predict \
  -H "Content-Type: application/json" \
  -d '{"data": ["[{\"role\":\"user\",\"content\":\"Hello!\"}]", 512, 0.7]}'
```

---

## Cost + Latency Table

| Model | Platform | Avg Latency | Cost/1K tokens | Cost/mo @100K |
|-------|----------|-------------|----------------|---------------|
| Qwen2.5-0.5B | HF Spaces Free CPU | 10–25s | $0.00 | $0.00 |
| Qwen2.5-0.5B | HF Spaces Pro GPU | 1–3s | ~$0.001 | ~$0.10 |
| Qwen2.5-0.5B | Modal A10G | 0.5–1.5s | ~$0.0006 | ~$0.06 |
| Qwen2.5-0.5B | RunPod RTX 3090 | 0.3–1.0s | ~$0.0004 | ~$0.04 |
| Qwen2.5-0.5B | Replicate | 1–4s | ~$0.0015 | ~$0.15 |
| GPT-4o-mini | OpenAI API | 1–3s | $0.00015 in / $0.0006 out | ~$0.075 |

---

## Generating the Evaluation PDF

```bash
uv run python generate_eval_report.py
# → outputs evaluation_report.pdf
```

Requires `OPENAI_API_KEY` in `.env`. The script runs the full 18-prompt evaluation and builds a multi-page PDF with summary metrics, charts, cost table, and detailed results.

---

## Design Decisions

| Decision | Rationale |
|---|---|
| **HF Space (Free CPU)** | Zero-cost public deployment; URL is stable for demo submissions. `Qwen2.5-0.5B` fits in CPU RAM. |
| **3-layer guardrails** | Keyword filter is instant; TF-IDF semantic layer catches paraphrased jailbreaks; LLM layer reserved for borderline cases (opt-in to control cost). |
| **Sliding window memory** | Simple, predictable context growth. Summary fallback prevents token explosion without losing key facts. |
| **TF-IDF over sentence-transformers** | No GPU, no external model download, no pip dependency. 5ms latency vs ~500ms for embedding models. Sufficient for policy enforcement. |
| **`urllib` for web search** | No API key, no third-party package. DuckDuckGo Instant Answer is free and sufficient for factual queries. |
| **JSONL for traces** | Append-only, no schema migrations, trivially parseable. Sufficient for single-node deployment; production would use a proper tracing backend (e.g. Langfuse, Braintrust). |
| **`compile()` not `eval()`** | Calculator safety — `compile()` with empty `__builtins__` prevents arbitrary code execution while still evaluating arithmetic. |

---

## Submission

**GitHub repo**: https://github.com/HarshRajj/ai-assistant-ollive  
**Demo link**: https://HarshRajj-ollive-arena.hf.space  
**OSS API**: https://HarshRajj-ollive-oss.hf.space  
**Email**: work@ollive.ai
