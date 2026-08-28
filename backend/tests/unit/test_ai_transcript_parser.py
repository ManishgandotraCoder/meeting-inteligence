import pytest

from app.core.exceptions import InvalidTranscriptError
from app.schemas.transcript import TranscriptParseOutput, TranscriptTurnOutput
from app.services.ai_transcript_parser import AiTranscriptParser, split_parse_windows
from app.services.transcript_parser import sequential_timestamp, turns_to_segments


class FakeLLM:
    def __init__(self, output: TranscriptParseOutput):
        self.output = output
        self.prompts: list[str] = []

    async def extract_transcript(self, _system: str, user_prompt: str) -> TranscriptParseOutput:
        self.prompts.append(user_prompt)
        return self.output


@pytest.mark.asyncio
async def test_ai_parser_maps_model_turns_and_normalizes_time():
    llm = FakeLLM(
        TranscriptParseOutput(
            segments=[
                TranscriptTurnOutput(
                    speaker="Maya Patel — Project Manager",
                    timestamp="9:30 AM",
                    text="Let's launch by 30 September.",
                ),
                TranscriptTurnOutput(
                    speaker="Daniel Kim",
                    timestamp=None,
                    text="Wireframes are ready Thursday.",
                ),
            ]
        )
    )

    segments = await AiTranscriptParser(llm).parse("messy meeting notes about a launch")

    assert segments[0].speaker == "Maya Patel"
    assert segments[0].start_time == "09:30:00"
    assert segments[1].speaker == "Daniel Kim"
    assert segments[1].start_time == sequential_timestamp(1)
    assert "launch" in segments[0].text


@pytest.mark.asyncio
async def test_ai_parser_rejects_empty_extraction():
    llm = FakeLLM(TranscriptParseOutput(segments=[]))

    with pytest.raises(InvalidTranscriptError):
        await AiTranscriptParser(llm).parse("random file with no dialogue")


def test_turns_to_segments_skips_blank_text():
    segments = turns_to_segments(
        [
            TranscriptTurnOutput(speaker="Sarah", timestamp="00:00:12", text="  "),
            TranscriptTurnOutput(speaker="John", timestamp="00:00:21", text="I own the API."),
        ]
    )

    assert len(segments) == 1
    assert segments[0].speaker == "John"


def test_split_parse_windows_keeps_short_text_whole():
    assert split_parse_windows("hello", size=20) == ["hello"]


def test_split_parse_windows_breaks_on_newlines():
    text = "aaaa\nbbbb\ncccc\ndddd"
    windows = split_parse_windows(text, size=10)
    assert windows
    assert "".join(windows).replace("\n", "") == "aaaabbbbccccdddd"
