# 🫒 Ollive AI Benchmarking Arena

A production-grade LLM benchmarking playground comparing **OpenAI GPT-4o-mini** (Frontier) against **Qwen 2.5** (Open Source) in a split-screen arena with streaming, safety guardrails, and human-in-the-loop evaluation.

## Quick Start

```bash
# 1. Clone & enter the project
git clone <repo-url> && cd ai-assistant-ollive

# 2. Copy environment template and fill in your keys
cp .env.example .env
#    → Set OPENAI_API_KEY and HF_TOKEN in .env

# 3. Install dependencies (requires uv: https://docs.astral.sh/uv/)
uv sync

# 4. Launch the app
uv run streamlit run app.py
```

The app opens at **http://localhost:8501**.

> **No API keys?** You can also enter your OpenAI key at runtime via the sidebar password field — it's stored in volatile session memory only, never written to disk.

---

## Architecture

```
ai-assistant-ollive/
├── app.py                 ← Streamlit entry point, sidebar credential shield, page routing
├── config.py              ← Centralized env vars, model IDs, system prompt, utilities
├── guardrails.py          ← Input/output safety filters (jailbreak, prompt injection)
├── models/
│   ├── frontier_model.py  ← OpenAI GPT-4o-mini with real SSE streaming
│   └── oss_model.py       ← Qwen 2.5 via huggingface_hub InferenceClient
├── evaluator/
│   ├── dataset.py         ← 18 curated test prompts (Factual / Adversarial / Sensitive)
│   ├── judge.py           ← LLM-as-Judge scoring (GPT-4o-mini, 1-5 scale)
│   └── runner.py          ← Evaluation orchestrator
├── ui/
│   ├── styles.py          ← Premium CSS (glassmorphism, animations, dark theme)
│   ├── chat_page.py       ← Arena: split-screen with streaming + metrics + voting
│   └── eval_page.py       ← Evaluation dashboard with Plotly charts
├── .env.example           ← Template for API keys
├── pyproject.toml         ← uv project manifest
└── eval_log.jsonl         ← Human feedback votes (auto-generated)
```

### Design Decisions

| Decision | Rationale |
|---|---|
| **Streamlit over Next.js** | Eliminates infrastructure latency fragmentation — no REST/WebSocket boundary between frontend and model calls. Single-process Python keeps profiling clean. |
| **Hybrid credential shield** | Sidebar password field for reviewer convenience (volatile, in-memory) with env-var fallback for CI/deployment. No key ever touches disk. |
| **`huggingface_hub` over raw `requests`** | Official SDK handles retries, model-loading waits, and auth cleanly. One less thing to debug. |
| **`time.perf_counter()` over `time.time()`** | Monotonic, sub-microsecond resolution — immune to system clock adjustments. Essential for credible latency benchmarks. |
| **JSONL for feedback persistence** | Append-only, no schema migrations, trivially parseable. Good enough for a take-home; production would use a proper eval tracking table (see Future Work). |
| **Qwen 2.5 3B (default)** | HuggingFace free-tier Serverless Inference is unreliable for 7B+ models. 3B is configurable in `config.py`. |

### Trade-offs

- **OSS streaming**: The HuggingFace Serverless Inference API doesn't reliably support SSE streaming for all models. The OSS response renders after full completion rather than token-by-token. This is honest — no simulated streaming.
- **Token estimation**: Uses a `words × 1.33` heuristic rather than a proper tokenizer. Accurate enough for comparative benchmarks; not for billing.
- **Single-turn arena**: Each arena prompt is independent (no multi-turn memory) for cleaner benchmarking.

---

## Features

### 🏟️ Arena (Split-Screen Benchmarking)
- OpenAI streams token-by-token in the left column
- Qwen displays its full response in the right column
- `st.metric` widgets show **Latency** and **Est. Tokens** per model
- Human feedback vote (`st.radio`) persists to `eval_log.jsonl`

### 🛡️ Safety Guardrails
- Pre-flight input filter blocks jailbreak patterns (`"ignore previous instructions"`, `"bypass system"`, `"sudo"`, etc.)
- Post-generation output filter catches known harmful phrases
- All blocked inputs are logged with timestamps

### 📊 Evaluation Dashboard
- Automated LLM-as-Judge evaluation across 18 prompts (Factual / Adversarial / Sensitive)
- Plotly charts: score-by-category bar chart, latency-per-prompt line chart
- Human feedback log viewer

---

## Future Improvements

- **LangSmith / Braintrust eval tracking** — structured evaluation tables with version control
- **Vector logging** — embed prompts and responses for semantic retrieval and clustering
- **Prometheus / OpenTelemetry metrics** — export latency histograms, token throughput, error rates
- **Dedicated HF endpoint** — enable real streaming for the OSS tier
- **Multi-turn arena** — carry conversation context across prompts
- **A/B blind evaluation** — randomize column positions so the reviewer doesn't know which model is which
