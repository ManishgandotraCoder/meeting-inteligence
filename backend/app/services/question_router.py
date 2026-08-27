import re

QuestionKind = str

_ACTION = re.compile(
    r"\b(all\s+)?(the\s+)?(action items?|tasks? assigned|todos?)\b",
    re.IGNORECASE,
)
_DECISION = re.compile(
    r"\b(all\s+)?(the\s+)?decisions?\b|\bwhat (was|were|did we) decide\b",
    re.IGNORECASE,
)
_RISK = re.compile(
    r"\b(all\s+)?(the\s+)?(risks?|blockers?)\b",
    re.IGNORECASE,
)
_FOLLOWUP = re.compile(
    r"\b(it|that|this|they|them|those|he|she|his|her|accepted|rejected)\b|"
    r"^(and|what about|was it|did they)\b",
    re.IGNORECASE,
)


def classify_question(question: str) -> QuestionKind:
    if _ACTION.search(question):
        return "action_items"
    if _DECISION.search(question):
        return "decisions"
    if _RISK.search(question):
        return "risks"
    return "open"


def is_followup(question: str, history_length: int) -> bool:
    if history_length <= 0:
        return False
    return bool(_FOLLOWUP.search(question.strip())) or len(question.split()) <= 6
