from __future__ import annotations

import os
import shutil
import tempfile
from collections.abc import Iterable
from pathlib import Path
from threading import Lock

from app.core.config import settings
from app.core.exceptions import InvalidTranscriptError
from app.core.logging import logger

_model = None
_model_lock = Lock()
_FFMPEG_DIRS = ("/opt/homebrew/bin", "/usr/local/bin")


def format_timestamp(seconds: float) -> str:
    total = max(0, int(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def whisper_segments_to_transcript(
    segments: Iterable[tuple[float, str]],
    speaker: str = "Speaker",
) -> str:
    blocks: list[str] = []
    for start, text in segments:
        cleaned = " ".join(text.split())
        if not cleaned:
            continue
        blocks.append(f"[{format_timestamp(start)}] {speaker}:\n{cleaned}")

    if not blocks:
        raise InvalidTranscriptError("No speech was detected in the recording.")

    return "\n\n".join(blocks)


def _ensure_ffmpeg() -> None:
    path = os.environ.get("PATH", "")
    for directory in _FFMPEG_DIRS:
        binary = Path(directory) / "ffmpeg"
        if binary.exists() and directory not in path.split(":"):
            os.environ["PATH"] = f"{directory}:{path}"
            path = os.environ["PATH"]
    if shutil.which("ffmpeg") is None:
        raise InvalidTranscriptError(
            "ffmpeg is required for voice transcription. Install it with "
            "`brew install ffmpeg` (macOS) or your package manager."
        )


def _load_model():
    global _model
    with _model_lock:
        if _model is not None:
            return _model

        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise InvalidTranscriptError(
                "Voice transcription is not installed. Install ffmpeg and "
                '`pip install "faster-whisper"`.'
            ) from exc

        logger.info("whisper_model_loading", model=settings.whisper_model)
        _model = WhisperModel(
            settings.whisper_model,
            device="cpu",
            compute_type="int8",
        )
        return _model


class TranscriptionService:
    def transcribe(self, content: bytes, filename: str) -> str:
        _ensure_ffmpeg()

        suffix = Path(filename).suffix.lower() or ".webm"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(content)
            path = tmp.name

        try:
            model = _load_model()
            language = settings.whisper_language or None
            segments, info = model.transcribe(
                path,
                vad_filter=True,
                language=language,
            )
            parsed = [(segment.start, segment.text) for segment in segments]
            transcript = whisper_segments_to_transcript(parsed)
            logger.info(
                "whisper_transcribe_complete",
                filename=filename,
                language=getattr(info, "language", None),
                turns=len(parsed),
            )
            return transcript
        except InvalidTranscriptError:
            raise
        except Exception as exc:
            raise InvalidTranscriptError(
                "Could not transcribe this recording. Use a wav/mp3/m4a/webm file, "
                "and make sure ffmpeg is installed."
            ) from exc
        finally:
            Path(path).unlink(missing_ok=True)
