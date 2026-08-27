from app.llm.client import parse_model_json
from app.schemas.insights import RagAnswerOutput


def test_parse_model_json_reads_plain_object():
    result = parse_model_json(
        '{"answer":"Ship Friday","cited_chunk_ids":["c1"],"insufficient_evidence":false}',
        RagAnswerOutput,
    )

    assert result.answer == "Ship Friday"
    assert result.cited_chunk_ids == ["c1"]
    assert result.insufficient_evidence is False


def test_parse_model_json_strips_markdown_fence():
    result = parse_model_json(
        '```json\n{"answer":"No decision","cited_chunk_ids":[],"insufficient_evidence":true}\n```',
        RagAnswerOutput,
    )

    assert result.answer == "No decision"
    assert result.insufficient_evidence is True
