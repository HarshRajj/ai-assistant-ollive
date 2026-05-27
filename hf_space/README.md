---
title: Ollive OSS Model API
emoji: 🫒
colorFrom: purple
colorTo: indigo
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
license: apache-2.0
short_description: "Qwen2.5-0.5B-Instruct inference API for Ollive AI Arena"
---

# 🫒 Ollive OSS Model — Qwen2.5-0.5B-Instruct

This Space serves **Qwen2.5-0.5B-Instruct** as a JSON inference API for the
[Ollive AI Benchmarking Arena](https://github.com/HarshRajj/ai-assistant-ollive).

## API Usage

Send a POST request to `/run/predict` with:

```json
{
  "data": [
    [{"role": "user", "content": "Your prompt here"}],
    512,
    0.7
  ]
}
```

Returns:
```json
{
  "data": [
    {
      "text": "Model response",
      "latency": 2.34,
      "tokens": 42,
      "model": "Qwen/Qwen2.5-0.5B-Instruct"
    }
  ]
}
```

## Parameters

| Field | Type | Default | Description |
|---|---|---|---|
| `messages` | list | required | OpenAI-format message list |
| `max_tokens` | int | 512 | Max generation tokens |
| `temperature` | float | 0.7 | Sampling temperature |

## Safety

Input and output safety checks are applied on every request.
Blocked requests return a `guardrail_triggered: true` field in the response.

## Model Card

- **Base model**: [Qwen/Qwen2.5-0.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct)
- **Parameters**: 0.5 billion
- **Context**: 32K tokens
- **License**: Apache 2.0
