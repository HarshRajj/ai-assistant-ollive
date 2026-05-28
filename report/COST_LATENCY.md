# Cost and Latency Benchmarks

| Model | Platform | Avg Latency | Cost/1K tokens | Cost/mo @100K |
|-------|----------|-------------|----------------|---------------|
| Qwen2.5-0.5B | HF Spaces Free CPU | 10–25s | $0.00 | $0.00 |
| Qwen2.5-0.5B | HF Spaces Pro GPU | 1–3s | ~$0.001 | ~$0.10 |
| Qwen2.5-0.5B | Modal A10G | 0.5–1.5s | ~$0.0006 | ~$0.06 |
| Qwen2.5-0.5B | RunPod RTX 3090 | 0.3–1.0s | ~$0.0004 | ~$0.04 |
| Qwen2.5-0.5B | Replicate | 1–4s | ~$0.0015 | ~$0.15 |
| GPT-4o-mini | OpenAI API | 1–3s | $0.00015 in / $0.0006 out | ~$0.075 |

> **Note:** Open-source models require a fixed minimum compute cost (hosting instance) while Frontier API models run completely serverless. The numbers above assume 100K requests a month.
