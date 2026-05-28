"""
Evaluation Markdown Report Generator
====================================
Generates a professional Markdown report from the evaluation results.

Usage:
    uv run python generate_eval_report.py

Requires OPENAI_API_KEY in .env (for LLM-as-Judge scoring).
Outputs: report/EVAL_REPORT.md
"""

import os
import sys
import datetime
import statistics
from pathlib import Path
from dotenv import load_dotenv

from config import OSS_MODEL_ID, FRONTIER_MODEL_NAME

load_dotenv()

OUTPUT_PATH = Path("report") / "EVAL_REPORT.md"


def generate_report(results: list[dict], overall_oss: float, overall_fr: float, total_duration: float):
    if not results:
        print("❌ No evaluation results provided.")
        return

    # Create report directory if it doesn't exist
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Calculate average latencies
    avg_oss_lat = statistics.mean([r["oss_latency"] for r in results])
    avg_fr_lat = statistics.mean([r["frontier_latency"] for r in results])

    # Build the markdown content
    md = []
    md.append("# 🫒 Ollive Evaluation Report")
    md.append(f"**Date:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    
    md.append("## 🏆 Overall Performance")
    md.append("| Metric | OSS Model | Frontier Model |")
    md.append("|--------|-----------|----------------|")
    md.append(f"| **Model ID** | `{OSS_MODEL_ID}` | `{FRONTIER_MODEL_NAME}` |")
    md.append(f"| **Judge Score (out of 5)** | **{overall_oss:.2f}** | **{overall_fr:.2f}** |")
    md.append(f"| **Avg Latency** | {avg_oss_lat:.2f}s | {avg_fr_lat:.2f}s |")
    md.append("")
    
    md.append("## 📊 Detailed Breakdown")
    
    for i, r in enumerate(results, 1):
        md.append(f"### Prompt {i}: {r['category']}")
        md.append(f"> **Q:** {r['prompt']}\n")
        
        md.append("#### OSS Response")
        md.append(f"**Score:** {r['oss_score']}/5 | **Latency:** {r['oss_latency']:.2f}s | **Tokens/sec:** {r['oss_tps']:.1f}")
        md.append(f"```text\n{r['oss_response']}\n```\n")
        
        md.append("#### Frontier Response")
        md.append(f"**Score:** {r['frontier_score']}/5 | **Latency:** {r['frontier_latency']:.2f}s | **Tokens/sec:** {r['frontier_tps']:.1f}")
        md.append(f"```text\n{r['frontier_response']}\n```\n")
        
        md.append("#### Judge Rationale")
        md.append(f"_{r['judge_rationale']}_")
        md.append("---\n")

    md.append("## 🏗️ Architecture & Configuration Notes")
    from config import JUDGE_MODEL_NAME
    md.append("- **Guardrails:** 3-layer pipeline active (Pattern → Semantic → LLM)")
    md.append(f"- **Evaluator:** LLM-as-a-Judge using `{JUDGE_MODEL_NAME}`")
    md.append(f"- **Total Eval Duration:** {total_duration:.1f} seconds")

    # Write the markdown file
    OUTPUT_PATH.write_text("\n".join(md), encoding="utf-8")
    print(f"✅ Generated Evaluation Report: {OUTPUT_PATH}")


def main():
    if not os.environ.get("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not found in environment. Cannot run judge.")
        sys.exit(1)

    # Delay imports to avoid overhead if env var is missing
    from evaluator import run_evaluation

    print("🚀 Starting Evaluation Run...")
    start_time = datetime.datetime.now()
    
    results = run_evaluation(os.environ["OPENAI_API_KEY"])
    
    duration = (datetime.datetime.now() - start_time).total_seconds()
    
    if not results:
        print("❌ Evaluation failed.")
        sys.exit(1)

    oss_avg = statistics.mean([r["oss_score"] for r in results])
    fr_avg = statistics.mean([r["frontier_score"] for r in results])

    generate_report(results, oss_avg, fr_avg, duration)


if __name__ == "__main__":
    main()
