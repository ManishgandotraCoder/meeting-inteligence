import re

from app.core.exceptions import InvalidTranscriptError
from app.schemas.transcript import TranscriptSegmentCreate

HEADER_RE = re.compile(r"^\[(?P<timestamp>\d{2}:\d{2}:\d{2})\]\s*(?P<speaker>[^:]+):\s*$")


class TranscriptParser:
    def parse(self, raw_text: str) -> list[TranscriptSegmentCreate]:
        text = raw_text.strip()
        if not text:
            raise InvalidTranscriptError("Transcript is empty.")

        segments: list[TranscriptSegmentCreate] = []
        current_speaker: str | None = None
        current_time: str | None = None
        current_lines: list[str] = []

        def flush() -> None:
            nonlocal current_speaker, current_time, current_lines
            if current_speaker and current_time:
                content = "\n".join(current_lines).strip()
                if content:
                    segments.append(
                        TranscriptSegmentCreate(
                            speaker=current_speaker.strip(),
                            start_time=current_time,
                            text=content,
                            sequence_number=len(segments),
                        )
                    )
            current_lines = []

        for line in text.splitlines():
            match = HEADER_RE.match(line.strip())
            if match:
                flush()
                current_time = match.group("timestamp")
                current_speaker = match.group("speaker").strip()
            elif current_speaker is not None:
                current_lines.append(line)

        flush()

        if not segments:
            raise InvalidTranscriptError(
                "Could not parse transcript. Expected lines like '[00:00:12] Sarah:'."
            )

        for index in range(len(segments) - 1):
            segments[index].end_time = segments[index + 1].start_time

        return segments
