import re
from pathlib import Path
from time import monotonic

from app.core.config import settings
from app.core.exceptions import InvalidTranscriptError, RateLimitExceededError
from app.llm.prompts import LOW_CONFIDENCE_FALLBACK
from app.repositories.chunk_repository import RetrievedChunk

_SAFE_FILENAME = re.compile(r"[^A-Za-z0-9._-]+")
TEXT_EXTENSIONS = {".txt"}
AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".webm", ".ogg", ".mp4", ".mpeg", ".mpga"}


def classify_upload(filename: str | None) -> str:
    suffix = Path(filename or "").suffix.lower()
    if suffix in TEXT_EXTENSIONS:
        return "transcript"
    if suffix in AUDIO_EXTENSIONS:
        return "audio"
    raise InvalidTranscriptError(
        "Upload a .txt transcript or an audio file (.wav, .mp3, .m4a, .webm)."
    )


def sanitize_filename(filename: str | None) -> str:
    name = Path(filename or "transcript.txt").name
    cleaned = _SAFE_FILENAME.sub("_", name).strip("._") or "transcript.txt"
    classify_upload(cleaned)
    return cleaned


def validate_upload(filename: str | None, content: bytes) -> str:
    if classify_upload(filename) != "transcript":
        raise InvalidTranscriptError("Only .txt transcript files are supported here.")
    sanitize_filename(filename)
    if not content:
        raise InvalidTranscriptError("Transcript is empty.")
    if len(content) > settings.max_upload_size_mb * 1024 * 1024:
        raise InvalidTranscriptError(
            f"Transcript must be smaller than {settings.max_upload_size_mb} MB."
        )
    try:
        raw_text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InvalidTranscriptError("Transcript must be UTF-8 encoded text.") from exc

    if not raw_text.strip():
        raise InvalidTranscriptError("Transcript is empty.")
    if len(raw_text) > settings.max_transcript_chars:
        raise InvalidTranscriptError("Transcript is too long to process.")
    return raw_text


def validate_audio_upload(filename: str | None, content: bytes) -> None:
    if classify_upload(filename) != "audio":
        raise InvalidTranscriptError(
            "Upload a .txt transcript or an audio file (.wav, .mp3, .m4a, .webm)."
        )
    sanitize_filename(filename)
    if not content:
        raise InvalidTranscriptError("Recording is empty.")
    max_bytes = settings.max_audio_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise InvalidTranscriptError(
            f"Audio must be smaller than {settings.max_audio_upload_size_mb} MB."
        )


def validate_question(question: str) -> str:
    trimmed = question.strip()
    if not trimmed:
        raise InvalidTranscriptError("Question cannot be empty.")
    if len(trimmed) > settings.max_question_chars:
        raise InvalidTranscriptError("Question is too long.")
    return trimmed


def filter_cited_chunks(
    cited_ids: list[str],
    retrieved: list[RetrievedChunk],
) -> list[RetrievedChunk]:
    allowed = {chunk.id: chunk for chunk in retrieved}
    return [allowed[chunk_id] for chunk_id in cited_ids if chunk_id in allowed]


def low_confidence_response() -> str:
    return LOW_CONFIDENCE_FALLBACK


class InMemoryRateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, list[float]] = {}

    def hit(self, key: str) -> None:
        now = monotonic()
        recent = [stamp for stamp in self._hits.get(key, []) if now - stamp < self.window_seconds]
        if len(recent) >= self.max_requests:
            self._hits[key] = recent
            raise RateLimitExceededError("Too many requests. Please wait and try again.")
        recent.append(now)
        self._hits[key] = recent


upload_limiter = InMemoryRateLimiter(
    settings.upload_rate_limit,
    settings.rate_limit_window_seconds,
)
question_limiter = InMemoryRateLimiter(
    settings.question_rate_limit,
    settings.rate_limit_window_seconds,
)
