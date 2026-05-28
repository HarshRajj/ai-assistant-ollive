# Architecture Overview

## Engine Logic (`core/`)
The project has been restructured into a modular format. All heavy lifting happens in the `core/` package:
- **`core/memory.py`**: Manages the conversational context using LangChain's `ConversationSummaryBufferMemory`. It stores up to a specific window size of messages and compresses older messages using an LLM.
- **`core/guardrails.py`**: Implements a 3-layer safety pipeline:
  1. Pattern Matching (Regex/keywords for prompt injection)
  2. Semantic Matching (Soft-blocking harmful intents)
  3. LLM-as-a-Judge (GPT-4.1-nano based dynamic evaluation)
- **`core/tools.py`**: Exposes intent-based tool execution (Calculator, Web Search, DateTime).
- **`core/observability.py`**: Handles generating tracing IDs and logging inference details into `eval_log.jsonl`.

## UI (`ui/`)
- Streamlit powers the frontend. `ui/chat_page.py` renders the split-screen comparison between the Frontier Model (GPT-4o-mini) and the Open Source Model (Qwen 2.5).
- `ui/eval_page.py` reads the observability logs and generates latency and cost dashboards.

## Evaluator (`evaluator/`)
- Contains the static `dataset.py` of 18 test prompts.
- `judge.py` evaluates outputs using a prompt template from the `prompts/` directory.
- `runner.py` orchestrates the headless evaluation runs.
