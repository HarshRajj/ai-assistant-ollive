# 🫒 Ollive AI Benchmarking Arena

A production-grade LLM benchmarking playground comparing **OpenAI GPT-4o-mini** (Frontier) against **Qwen 2.5** (Open Source) in a split-screen arena with streaming, 3-layer safety guardrails, LangChain memory, tool use, structured observability, and an automated evaluation PDF.

[![HF Space](https://img.shields.io/badge/🤗%20HF%20Space-OSS%20Model-blue)](https://HarshRajj-ollive-oss.hf.space)
[![Streamlit App](https://img.shields.io/badge/Streamlit-Demo-red)](https://HarshRajj-ollive-arena.hf.space)

---

## ⚡ Quick Start

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

## 🏗️ Architecture

The codebase follows a modular structure to ensure maintainability and separation of concerns.

```
ai-assistant-ollive/
├── app.py                   ← Streamlit entry point, sidebar, page routing
├── config.py                ← Centralized env vars, model IDs, COST_TABLE
│
├── prompts/                 ← Modular prompt templates
│   ├── system.py            ← Shared system prompt
│   ├── judge.py             ← LLM-as-Judge evaluation prompt
│   └── safety.py            ← Safety classifier prompt
│
├── models/                  ← Model clients
│   ├── frontier_model.py    ← GPT-4o-mini with SSE streaming + observability
│   └── oss_model.py         ← Qwen 2.5 via HF Space API (+ HF Inference fallback)
│
├── evaluator/               ← Evaluation pipeline
│   ├── dataset.py           ← 18 curated test prompts
│   ├── judge.py             ← LLM-as-Judge (gpt-4.1-nano, 1-5 scale)
│   └── runner.py            ← Eval orchestrator with eval_run_id tracking
│
├── ui/                      ← Frontend logic
│   ├── styles.py            ← Premium CSS (glassmorphism, animations)
│   ├── chat_page.py         ← Arena: split-screen + memory + tools + guardrails
│   └── eval_page.py         ← 4-tab dashboard (Eval / Cost / Observability / Feedback)
│
├── tests/                   ← Pytest suite
│   ├── conftest.py
│   ├── test_guardrails.py
│   ├── test_memory.py
│   ├── test_tools.py
│   └── test_evaluator.py
│
├── guardrails.py            ← 3-layer safety pipeline (pattern→semantic→LLM)
├── memory.py                ← LangChain ConversationSummaryBufferMemory wrapper
├── observability.py         ← InferenceTrace dataclass, JSONL logging, analytics
├── tools.py                 ← Safe calculator, DuckDuckGo search, datetime
├── generate_eval_report.py  ← Headless eval → PDF via reportlab
│
└── hf_space/                ← OSS Model deployment package (Gradio REST API)
```

---

## ✨ Features

### 🏟️ Arena (Split-Screen Benchmarking)
- OpenAI streams token-by-token (left column)
- Qwen 2.5 renders full response (right column)
- Human feedback vote persists to `eval_log.jsonl`

### 🧠 LangChain Memory
- **`ConversationSummaryBufferMemory`** strategy — older turns compressed via an LLM when the buffer exceeds token threshold.

### 🛡️ Safety Guardrails (3-Layer)
| Layer | Method | Latency |
|-------|--------|---------|
| 1 — Pattern | Keyword/regex block list (28 patterns) | < 1ms |
| 2 — Semantic | Expanded harmful-intent keyword matching | ~5ms |
| 3 — LLM Judge | GPT-4.1-nano binary safety classifier (opt-in) | ~500ms |

### 🔧 Tool Use
Tools are resolved via Intent-detection and result injected into the context.
- **Calculator**: Safe arithmetic eval using `compile()` (no arbitrary `eval()`).
- **Web Search**: DuckDuckGo Instant Answer API (free, no API key).
- **DateTime**: Current date/time info.

### 📊 Evaluation Dashboard & PDF Report
- **LLM-as-Judge**: Scored using **`gpt-4.1-nano`** to reduce self-evaluation bias.
- **Observability**: Inference trace viewer showing percentiles (p50/p90) and error rates.
- **PDF Generation**: Run `uv run python generate_eval_report.py` to auto-generate a comprehensive metrics PDF.

---

## 💰 Cost + Latency

| Model | Platform | Avg Latency | Cost/1K tokens | Cost/mo @100K |
|-------|----------|-------------|----------------|---------------|
| Qwen2.5-0.5B | HF Spaces Free CPU | 10–25s | $0.00 | $0.00 |
| Qwen2.5-0.5B | HF Spaces Pro GPU | 1–3s | ~$0.001 | ~$0.10 |
| Qwen2.5-0.5B | Modal A10G | 0.5–1.5s | ~$0.0006 | ~$0.06 |
| Qwen2.5-0.5B | RunPod RTX 3090 | 0.3–1.0s | ~$0.0004 | ~$0.04 |
| Qwen2.5-0.5B | Replicate | 1–4s | ~$0.0015 | ~$0.15 |
| GPT-4o-mini | OpenAI API | 1–3s | $0.00015 in / $0.0006 out | ~$0.075 |

---

## 🧪 Testing

```bash
uv run pytest tests/ -v
```

---

## 📦 OSS Model Deployment

The OSS model is deployed as a **HuggingFace Space** at:
`https://HarshRajj-ollive-oss.hf.space`

```bash
curl -X POST https://HarshRajj-ollive-oss.hf.space/run/predict \
  -H "Content-Type: application/json" \
  -d '{"data": ["[{\"role\":\"user\",\"content\":\"Hello!\"}]", 512, 0.7]}'
```
