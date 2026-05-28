"""Prompts package for Ollive AI Arena."""

from prompts.system import SYSTEM_PROMPT
from prompts.judge import JUDGE_PROMPT_TEMPLATE
from prompts.safety import SAFETY_CLASSIFIER_PROMPT

__all__ = ["SYSTEM_PROMPT", "JUDGE_PROMPT_TEMPLATE", "SAFETY_CLASSIFIER_PROMPT"]
