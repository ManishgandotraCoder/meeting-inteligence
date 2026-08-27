from pathlib import Path

from app.services.transcript_parser import TranscriptParser


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
