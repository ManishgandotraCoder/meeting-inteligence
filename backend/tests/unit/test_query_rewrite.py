from app.schemas.chat import ChatHistoryMessage
from app.services.query_rewrite import heuristic_rewrite
from app.services.question_router import classify_question, is_followup


def test_classifies_catalog_questions():
    assert classify_question("What are all the action items?") == "action_items"
    assert classify_question("What decisions were made?") == "decisions"
    assert classify_question("What risks or blockers were discussed?") == "risks"
    assert classify_question("Did Rahul's proposal get accepted?") == "open"


def test_followup_detection_and_rewrite():
    history = [
        ChatHistoryMessage(role="user", content="What did Rahul propose?"),
        ChatHistoryMessage(role="assistant", content="He proposed delaying launch."),
    ]
    question = "Was it accepted?"
    assert is_followup(question, len(history))
    rewritten = heuristic_rewrite(question, history)
    assert "Rahul" in rewritten or "previous question" in rewritten
    assert "accepted" in rewritten.lower()
