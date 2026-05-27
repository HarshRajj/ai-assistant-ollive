"""
Evaluation PDF Report Generator
================================
Generates a professional PDF report from the evaluation results.

Usage:
    uv run python generate_eval_report.py

Requires OPENAI_API_KEY in .env (for LLM-as-Judge scoring).
Outputs: evaluation_report.pdf
"""

import os
import sys
import json
import datetime
import statistics
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Check for reportlab
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, PageBreak,
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
except ImportError:
    print("❌ reportlab not installed. Run: uv add reportlab")
    sys.exit(1)

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("⚠️  matplotlib not found — charts will be skipped.")

from config import OSS_MODEL_ID, FRONTIER_MODEL_NAME
from ui.eval_page import COST_TABLE


# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------
PURPLE = colors.HexColor("#667eea")
DARK_PURPLE = colors.HexColor("#764ba2")
BG_DARK = colors.HexColor("#0e0e1a")
BG_CARD = colors.HexColor("#1a1a2e")
WHITE = colors.white
GRAY = colors.HexColor("#888888")
GREEN = colors.HexColor("#43e97b")
RED = colors.HexColor("#fa709a")

OUTPUT_PATH = Path("evaluation_report.pdf")
CHART_DIR = Path("_report_charts")


# ---------------------------------------------------------------------------
# Chart generation
# ---------------------------------------------------------------------------

def _make_score_chart(results: list[dict]) -> Path | None:
    if not HAS_MATPLOTLIB:
        return None

    CHART_DIR.mkdir(exist_ok=True)

    from collections import defaultdict
    cat_oss: dict[str, list] = defaultdict(list)
    cat_fr: dict[str, list] = defaultdict(list)
    for r in results:
        cat_oss[r["category"]].append(r["oss_score"])
        cat_fr[r["category"]].append(r["frontier_score"])

    cats = sorted(cat_oss.keys())
    oss_means = [statistics.mean(cat_oss[c]) for c in cats]
    fr_means = [statistics.mean(cat_fr[c]) for c in cats]

    fig, ax = plt.subplots(figsize=(9, 4))
    fig.patch.set_facecolor("#0e0e1a")
    ax.set_facecolor("#1a1a2e")

    x = range(len(cats))
    w = 0.35
    bars1 = ax.bar([i - w/2 for i in x], oss_means, w, label="OSS (Qwen 2.5)", color="#667eea")
    bars2 = ax.bar([i + w/2 for i in x], fr_means, w, label="Frontier (GPT-4o-mini)", color="#764ba2")

    ax.set_xticks(list(x))
    ax.set_xticklabels(cats, color="white", fontsize=9)
    ax.set_ylim(0, 5.5)
    ax.set_ylabel("Score (1-5)", color="white")
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_edgecolor("#444")
    ax.legend(facecolor="#1a1a2e", edgecolor="#667eea", labelcolor="white", fontsize=9)

    for bar in bars1:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                f"{bar.get_height():.1f}", ha="center", color="white", fontsize=8)
    for bar in bars2:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                f"{bar.get_height():.1f}", ha="center", color="white", fontsize=8)

    plt.tight_layout()
    path = CHART_DIR / "score_by_category.png"
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    return path


def _make_latency_chart(results: list[dict]) -> Path | None:
    if not HAS_MATPLOTLIB:
        return None

    CHART_DIR.mkdir(exist_ok=True)
    oss_lats = [r["oss_latency"] for r in results]
    fr_lats = [r["frontier_latency"] for r in results]

    fig, ax = plt.subplots(figsize=(9, 3.5))
    fig.patch.set_facecolor("#0e0e1a")
    ax.set_facecolor("#1a1a2e")

    xs = list(range(1, len(results) + 1))
    ax.plot(xs, oss_lats, "o-", color="#667eea", linewidth=1.5, markersize=4, label="OSS")
    ax.plot(xs, fr_lats, "o-", color="#764ba2", linewidth=1.5, markersize=4, label="Frontier")

    ax.set_xlabel("Prompt #", color="white")
    ax.set_ylabel("Latency (s)", color="white")
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_edgecolor("#444")
    ax.legend(facecolor="#1a1a2e", edgecolor="#667eea", labelcolor="white", fontsize=9)

    plt.tight_layout()
    path = CHART_DIR / "latency_per_prompt.png"
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    return path


# ---------------------------------------------------------------------------
# PDF builder
# ---------------------------------------------------------------------------

def build_pdf(results: list[dict]) -> None:
    doc = SimpleDocTemplate(
        str(OUTPUT_PATH),
        pagesize=A4,
        leftMargin=2*cm,
        rightMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    TITLE = ParagraphStyle("Title", parent=styles["Title"],
                           fontName="Helvetica-Bold", fontSize=22,
                           textColor=PURPLE, spaceAfter=6)
    SUBTITLE = ParagraphStyle("Subtitle", parent=styles["Normal"],
                              fontSize=11, textColor=GRAY, spaceAfter=14)
    H1 = ParagraphStyle("H1", parent=styles["Heading1"],
                         fontName="Helvetica-Bold", fontSize=14,
                         textColor=PURPLE, spaceBefore=14, spaceAfter=6)
    H2 = ParagraphStyle("H2", parent=styles["Heading2"],
                         fontName="Helvetica-Bold", fontSize=11,
                         textColor=DARK_PURPLE, spaceBefore=8, spaceAfter=4)
    BODY = ParagraphStyle("Body", parent=styles["Normal"],
                           fontSize=9, leading=13, textColor=colors.black)
    SMALL = ParagraphStyle("Small", parent=styles["Normal"],
                            fontSize=8, leading=11, textColor=GRAY)

    story = []
    now = datetime.datetime.now().strftime("%B %d, %Y — %H:%M")

    # ---- Cover ----
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph("🫒 Ollive AI Benchmarking Arena", TITLE))
    story.append(Paragraph("Evaluation Report", SUBTITLE))
    story.append(Paragraph(f"Generated: {now}", SMALL))
    story.append(HRFlowable(width="100%", thickness=1, color=PURPLE, spaceAfter=10))

    # ---- Summary ----
    story.append(Paragraph("Executive Summary", H1))

    oss_scores = [r["oss_score"] for r in results]
    fr_scores = [r["frontier_score"] for r in results]
    oss_lats = [r["oss_latency"] for r in results]
    fr_lats = [r["frontier_latency"] for r in results]

    summary_data = [
        ["Metric", f"OSS ({OSS_MODEL_ID.split('/')[-1]})", f"Frontier ({FRONTIER_MODEL_NAME})"],
        ["Avg Score (1-5)", f"{statistics.mean(oss_scores):.2f}", f"{statistics.mean(fr_scores):.2f}"],
        ["Max Score", str(max(oss_scores)), str(max(fr_scores))],
        ["Min Score", str(min(oss_scores)), str(min(fr_scores))],
        ["Avg Latency (s)", f"{statistics.mean(oss_lats):.3f}", f"{statistics.mean(fr_lats):.3f}"],
        ["Max Latency (s)", f"{max(oss_lats):.3f}", f"{max(fr_lats):.3f}"],
        ["Total Prompts", str(len(results)), str(len(results))],
    ]
    t = Table(summary_data, colWidths=[6*cm, 5.5*cm, 5.5*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PURPLE),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f9f9ff"), WHITE]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#ddddee")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5*cm))

    # ---- Score chart ----
    score_chart = _make_score_chart(results)
    if score_chart:
        story.append(Paragraph("Score by Category", H1))
        from reportlab.platypus import Image as RLImage
        story.append(RLImage(str(score_chart), width=16*cm, height=7*cm))
        story.append(Spacer(1, 0.3*cm))

    # ---- Latency chart ----
    lat_chart = _make_latency_chart(results)
    if lat_chart:
        story.append(Paragraph("Latency per Prompt", H1))
        from reportlab.platypus import Image as RLImage
        story.append(RLImage(str(lat_chart), width=16*cm, height=5.5*cm))

    story.append(PageBreak())

    # ---- Cost + Latency table ----
    story.append(Paragraph("Cost + Latency Comparison", H1))
    story.append(Paragraph(
        "Estimated pricing across deployment platforms (May 2025). "
        "This project uses HF Spaces Free CPU for zero-cost public deployment.",
        BODY,
    ))
    story.append(Spacer(1, 0.3*cm))

    cost_headers = ["Model", "Platform", "Avg Latency", "Cost/1K tok", "Cost/mo @100K"]
    cost_rows = [cost_headers]
    for row in COST_TABLE:
        cost_rows.append([
            row["Model"],
            row["Platform"],
            row["Avg Latency (s)"],
            row["Cost / 1K tokens"],
            row["Cost / Month @ 100K tok"],
        ])
    ct = Table(cost_rows, colWidths=[3.5*cm, 4.5*cm, 2.5*cm, 2.5*cm, 3.5*cm])
    ct.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK_PURPLE),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f0f0ff"), WHITE]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#ccccdd")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(ct)
    story.append(Spacer(1, 0.5*cm))

    # ---- Detailed results ----
    story.append(Paragraph("Detailed Evaluation Results", H1))
    detail_headers = ["#", "Category", "Prompt (truncated)", "OSS Score", "Frontier Score"]
    detail_rows = [detail_headers]
    for i, r in enumerate(results, 1):
        detail_rows.append([
            str(i),
            r["category"],
            r["prompt"][:55] + ("…" if len(r["prompt"]) > 55 else ""),
            str(r["oss_score"]),
            str(r["frontier_score"]),
        ])
    dt = Table(detail_rows, colWidths=[0.8*cm, 4*cm, 7*cm, 1.8*cm, 2*cm])
    dt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PURPLE),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f9f9ff"), WHITE]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#ddddee")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("ALIGN", (3, 0), (-1, -1), "CENTER"),
    ]))
    story.append(dt)
    story.append(Spacer(1, 0.5*cm))

    # ---- Architecture notes ----
    story.append(PageBreak())
    story.append(Paragraph("Architecture & Design Decisions", H1))
    arch_items = [
        ("OSS Deployment", f"HuggingFace Spaces (Free CPU) — {OSS_MODEL_ID}. "
         "Gradio REST API with input/output safety guardrails embedded."),
        ("Evaluation Method", "LLM-as-Judge using GPT-4o-mini (temp=0) scoring responses 1-5 "
         "across Hallucination Rate, Content Safety, and Bias dimensions."),
        ("Safety Guardrails", "3-layer pipeline: (1) Exact phrase block list (jailbreaks), "
         "(2) Expanded harmful-intent keyword matching (paraphrased attacks), "
         "(3) Optional LLM meta-judge (GPT-4o-mini binary classifier)."),
        ("Observability", "Structured InferenceTrace records logged to traces.jsonl on every "
         "model call. Metrics: latency p50/p90/p99, tokens/s, error rate, guardrail rate."),
        ("Memory", "Sliding-window ConversationMemory (configurable size). "
         "Older turns auto-summarized via GPT-4o-mini when buffer exceeds threshold."),
        ("Tool Use", "Intent-detection dispatcher for 3 tools: safe calculator (no eval()), "
         "DuckDuckGo Instant Answer (no API key), and datetime. Results injected into context."),
    ]
    for title, desc in arch_items:
        story.append(Paragraph(f"<b>{title}</b>: {desc}", BODY))
        story.append(Spacer(1, 0.25*cm))

    # ---- Footer ----
    story.append(HRFlowable(width="100%", thickness=1, color=PURPLE))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "Ollive AI Benchmarking Arena — Built for the Founding AI/ML Engineer Assessment. "
        f"Report generated {now}.",
        SMALL,
    ))

    doc.build(story)
    print(f"✅ Report saved to: {OUTPUT_PATH}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    if not openai_key:
        print("❌ OPENAI_API_KEY not set in .env")
        sys.exit(1)

    print("🚀 Running evaluation suite…")
    from evaluator.runner import run_evaluation
    results = run_evaluation(openai_key=openai_key)

    print(f"✅ Evaluation complete — {len(results)} results")
    print("📄 Building PDF report…")
    build_pdf(results)


if __name__ == "__main__":
    main()
