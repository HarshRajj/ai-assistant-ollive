"""Evaluator package — test dataset, LLM-as-Judge, and evaluation runner."""

from evaluator.dataset import TEST_PROMPTS, CATEGORIES
from evaluator.judge import judge_response
from evaluator.runner import run_evaluation

__all__ = ["TEST_PROMPTS", "CATEGORIES", "judge_response", "run_evaluation"]
