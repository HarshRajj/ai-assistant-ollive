"""
Evaluation runner — orchestrates querying both models and scoring with the judge.
Now supports eval_run_id tracking and per-call observability logging.
"""

from evaluator.dataset import TEST_PROMPTS
from evaluator.judge import judge_response
from models.oss_model import query_oss_model_headless
from models.frontier_model import query_frontier_model
from core.observability import new_eval_run_id, make_trace, log_trace


def run_evaluation(openai_key: str) -> list[dict]:
    """Run all test prompts through both models and score with LLM-as-Judge.

    Args:
        openai_key: Resolved OpenAI API key for both the frontier model and judge.

    Returns:
        List of result dicts with keys: category, prompt, oss_response,
        frontier_response, oss_score, frontier_score, oss_latency,
        frontier_latency, oss_tokens, frontier_tokens, oss_reason,
        frontier_reason, eval_run_id.
    """
    run_id = new_eval_run_id()
    results: list[dict] = []

    for item in TEST_PROMPTS:
        messages = [{"role": "user", "content": item["prompt"]}]
        cat = item["category"]

        # Query both models (each logs its own trace via observability)
        oss_resp, oss_lat, oss_tokens = query_oss_model_headless(
            messages, eval_run_id=run_id, category=cat
        )
        fr_resp, fr_lat, fr_tokens = query_frontier_model(
            messages, openai_key, eval_run_id=run_id, category=cat
        )

        # Judge both responses
        oss_judge = judge_response(
            cat, item["prompt"], item["expected_keywords"],
            oss_resp, api_key=openai_key,
        )
        fr_judge = judge_response(
            cat, item["prompt"], item["expected_keywords"],
            fr_resp, api_key=openai_key,
        )

        results.append({
            "eval_run_id": run_id,
            "category": cat,
            "prompt": item["prompt"],
            "oss_response": oss_resp,
            "frontier_response": fr_resp,
            "oss_score": oss_judge["score"],
            "frontier_score": fr_judge["score"],
            "oss_reason": oss_judge["reason"],
            "frontier_reason": fr_judge["reason"],
            "oss_latency": round(oss_lat, 3),
            "frontier_latency": round(fr_lat, 3),
            "oss_tokens": oss_tokens,
            "frontier_tokens": fr_tokens,
        })

    return results
