"""Centralized prompts module for SmartDiner AI services."""

from app.prompts.intent_classification import INTENT_CLASSIFICATION_PROMPT
from app.prompts.constraint_extraction import (
    CONSTRAINT_EXTRACTION_SYSTEM_PROMPT
)
from app.prompts.explanation import (
    EXPLANATION_SYSTEM_PROMPT,
    QUESTION_ANSWER_SYSTEM_PROMPT,
)
from app.prompts.admin_insights import (
    ADMIN_INSIGHTS_SYSTEM_PROMPT,
    ADMIN_CLASSIFIER_PROMPT,
)
from app.prompts.llm_judge import JUDGE_SYSTEM_PROMPT

__all__ = [
    "INTENT_CLASSIFICATION_PROMPT",
    "CONSTRAINT_EXTRACTION_SYSTEM_PROMPT",
    "EXPLANATION_SYSTEM_PROMPT",
    "QUESTION_ANSWER_SYSTEM_PROMPT",
    "ADMIN_INSIGHTS_SYSTEM_PROMPT",
    "ADMIN_CLASSIFIER_PROMPT",
    "JUDGE_SYSTEM_PROMPT",
]