import pytest

from app.core.exceptions import InvalidTranscriptError, RateLimitExceededError
from app.llm.prompts import LOW_CONFIDENCE_FALLBACK
from app.services.guardrails import (
    InMemoryRateLimiter,
    classify_upload,
    sanitize_filename,
    validate_audio_upload,
    validate_question,
    validate_upload,
)


def test_sanitize_filename_strips_paths_and_requires_supported_type():
    assert sanitize_filename("../../etc/passwd.txt") == "passwd.txt"
    assert sanitize_filename("standup.webm") == "standup.webm"
    with pytest.raises(InvalidTranscriptError):
        sanitize_filename("notes.pdf")


def test_classify_upload_splits_text_and_audio():
    assert classify_upload("notes.txt") == "transcript"
    assert classify_upload("kickoff.m4a") == "audio"
    with pytest.raises(InvalidTranscriptError):
        classify_upload("slides.pdf")


def test_validate_audio_upload_rejects_empty_and_non_audio():
    with pytest.raises(InvalidTranscriptError):
        validate_audio_upload("standup.webm", b"")
    with pytest.raises(InvalidTranscriptError):
        validate_audio_upload("notes.txt", b"not-audio")


def test_validate_upload_rejects_empty_and_non_utf8():
    with pytest.raises(InvalidTranscriptError):
        validate_upload("meeting.txt", b"")
    with pytest.raises(InvalidTranscriptError):
        validate_upload("meeting.txt", b"\xff\xfe")


def test_validate_question_rejects_blank():
    with pytest.raises(InvalidTranscriptError):
        validate_question("   ")


def test_rate_limiter_blocks_excess_requests():
    limiter = InMemoryRateLimiter(max_requests=2, window_seconds=60)
    limiter.hit("user-1")
    limiter.hit("user-1")
    with pytest.raises(RateLimitExceededError):
        limiter.hit("user-1")


def test_fallback_copy_is_safe():
    assert "evidence" in LOW_CONFIDENCE_FALLBACK.lower()
