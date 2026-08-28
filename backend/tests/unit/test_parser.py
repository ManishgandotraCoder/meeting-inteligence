from pathlib import Path

from app.services.transcript_parser import (
    TranscriptParser,
    normalize_speaker,
    normalize_timestamp,
)


def test_parser_reads_speakers_and_timestamps():
    raw = Path("tests/fixtures/sample_meeting.txt").read_text()
    segments = TranscriptParser().parse(raw)

    assert len(segments) == 4
    assert segments[0].speaker == "Sarah"
    assert segments[0].start_time == "00:00:12"
    assert segments[1].speaker == "John"


def test_parser_keeps_multiline_utterance_together():
    raw = """[00:00:10] Sarah:
First line.
Second line.

[00:00:20] John:
Hello.
"""
    segments = TranscriptParser().parse(raw)

    assert len(segments) == 2
    assert "First line.\nSecond line." == segments[0].text


def test_parser_reads_chat_export_with_ampm_timestamps():
    raw = Path("tests/fixtures/project_discussion_chat.txt").read_text()
    segments = TranscriptParser().parse(raw)

    assert len(segments) == 17
    assert segments[0].speaker == "Maya Patel"
    assert segments[0].start_time == "09:30:00"
    assert segments[0].text.startswith("Good morning, everyone!")
    assert segments[1].speaker == "Daniel Kim"
    assert segments[1].start_time == "09:32:00"
    assert segments[4].start_time == "09:38:00"
    assert "30 September: Website launch" in segments[4].text
    assert segments[-1].speaker == "Maya Patel"
    assert segments[-1].start_time == "10:00:00"
    assert {item.speaker for item in segments} == {
        "Maya Patel",
        "Daniel Kim",
        "Sofia Martinez",
        "Marcus Johnson",
    }


def test_normalize_timestamp_converts_12_hour_clock():
    assert normalize_timestamp("9:30 AM") == "09:30:00"
    assert normalize_timestamp("10:00 AM") == "10:00:00"
    assert normalize_timestamp("12:00 AM") == "00:00:00"
    assert normalize_timestamp("12:15 PM") == "12:15:00"
    assert normalize_timestamp("1:05 pm") == "13:05:00"
    assert normalize_timestamp("00:00:12") == "00:00:12"
    assert normalize_timestamp("9:30") == "09:30:00"
    assert normalize_timestamp("not a time") is None


def test_normalize_speaker_strips_role_and_colon():
    assert normalize_speaker("Sarah:") == "Sarah"
    assert normalize_speaker("Maya Patel — Project Manager") == "Maya Patel"
    assert normalize_speaker("Daniel Kim - UI/UX Designer") == "Daniel Kim"


def test_parser_reads_same_line_and_zoom_style_turns():
    raw = """[00:00:12] Sarah: We need to release the payments feature next Friday.
00:00:21 John: I can finish the API work by Wednesday.
"""
    segments = TranscriptParser().parse(raw)

    assert [item.speaker for item in segments] == ["Sarah", "John"]
    assert segments[0].start_time == "00:00:12"
    assert segments[1].start_time == "00:00:21"
    assert "payments feature" in segments[0].text


def test_parser_reads_name_colon_turns_without_timestamps():
    raw = """Sarah: We should ship Friday.
John: I will own the API.
Mike: The risk is Stripe.
"""
    segments = TranscriptParser().parse(raw)

    assert [item.speaker for item in segments] == ["Sarah", "John", "Mike"]
    assert segments[0].start_time == "00:00:00"
    assert segments[1].start_time == "00:00:05"
    assert "Stripe" in segments[2].text


def test_parser_reads_name_header_with_body_on_following_lines():
    raw = """Sarah:
We should ship Friday.

John:
I will own the API.
"""
    segments = TranscriptParser().parse(raw)

    assert [item.speaker for item in segments] == ["Sarah", "John"]
    assert segments[0].text == "We should ship Friday."


def test_try_parse_returns_empty_for_unstructured_notes():
    raw = """Meeting notes
We talked about the launch date and someone will own the API.
Stripe came up as a risk.
"""
    assert TranscriptParser().try_parse(raw) == []
