import json
from pathlib import Path

from app.services.question_router import classify_question


def test_eval_dataset_covers_required_question_types():
    payload = json.loads(Path("tests/fixtures/eval_questions.json").read_text())
    kinds = {item["kind"] for item in payload}
    ids = {item["id"] for item in payload}

    assert {"open", "decisions", "action_items"} <= kinds
    assert {"direct-fact", "follow-up", "missing-info", "prompt-injection"} <= ids
    for item in payload:
        assert classify_question(item["question"]) == item["kind"]
