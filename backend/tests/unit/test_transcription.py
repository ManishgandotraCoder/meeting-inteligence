import pytest

from app.core.exceptions import InvalidTranscriptError
from app.services.transcription_service import (
    format_timestamp,
    whisper_segments_to_transcript,
)


def test_format_timestamp_pads_hours_minutes_seconds():
    assert format_timestamp(0) == "00:00:00"
    assert format_timestamp(12) == "00:00:12"
    assert format_timestamp(81) == "00:01:21"
    assert format_timestamp(3723) == "01:02:03"


def test_whisper_segments_to_transcript_uses_parser_format():
    text = whisper_segments_to_transcript(
        [
            (12.4, "  We should ship Friday.  "),
            (21.0, "I can finish the API."),
            (30.0, "   "),
        ]
    )

    assert text == (
        "[00:00:12] Speaker:\nWe should ship Friday.\n\n"
        "[00:00:21] Speaker:\nI can finish the API."
    )


def test_whisper_segments_to_transcript_rejects_silence():
    with pytest.raises(InvalidTranscriptError):
        whisper_segments_to_transcript([(0.0, "   ")])
