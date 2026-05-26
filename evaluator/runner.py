"""
Evaluation runner — orchestrates querying both models and scoring with the judge.
"""

from evaluator.dataset import TEST_PROMPTS
from evaluator.judge import judge_response
from models.oss_model import query_oss_model_headless
from models.frontier_model import query_frontier_model


def run_evaluation(openai_key: str) -> list[dict]:
    """Run all test prompts through both models and score with LLM-as-Judge.

    Args:
        openai_key: Resolved OpenAI API key for both the frontier model and judge.

    Returns:
        List of result dicts with keys: category, prompt, oss_response,
        frontier_response, oss_score, frontier_score, oss_latency,
        frontier_latency, oss_tokens, frontier_tokens, oss_reason, frontier_reason.
    """
    results: list[dict] = []

    for item in TEST_PROMPTS:
        messages = [{"role": "user", "content": item["prompt"]}]

        # Query both models
        oss_resp, oss_lat, oss_tokens = query_oss_model_headless(messages)
        fr_resp, fr_lat, fr_tokens = query_frontier_model(messages, openai_key)

        # Judge both responses
        oss_judge = judge_response(
            item["category"], item["prompt"], item["expected_keywords"],
            oss_resp, api_key=openai_key,
        )
        fr_judge = judge_response(
            item["category"], item["prompt"], item["expected_keywords"],
            fr_resp, api_key=openai_key,
        )

        results.append({
            "category": item["category"],
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
