import re

from app.core.exceptions import InvalidTranscriptError
from app.schemas.transcript import TranscriptSegmentCreate, TranscriptTurnOutput

HEADER_RE = re.compile(
    r"^\[(?P<clock>[^\]]+)\]\s*(?P<speaker>[^:]+)\s*:?\s*(?P<body>.*)$"
)
ZOOM_RE = re.compile(
    r"^(?P<clock>\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?)\s+"
    r"(?P<speaker>[^:]+):\s*(?P<body>.*)$"
)
NAME_TURN_RE = re.compile(
    r"^(?P<speaker>[A-Z][\w'.-]*(?:\s+[A-Z][\w'.-]*){0,3})\s*:\s*(?P<body>.*)$"
)
CLOCK_HMS_RE = re.compile(r"^(?P<h>\d{1,2}):(?P<m>\d{2}):(?P<s>\d{2})$")
CLOCK_12H_RE = re.compile(
    r"^(?P<h>\d{1,2}):(?P<m>\d{2})(?::(?P<s>\d{2}))?\s*(?P<ampm>[AaPp][Mm])$"
)
CLOCK_HM_RE = re.compile(r"^(?P<h>\d{1,2}):(?P<m>\d{2})$")
ROLE_SPLIT_RE = re.compile(r"\s+[—–-]\s+")


def normalize_timestamp(clock: str) -> str | None:
    value = " ".join(clock.strip().split())

    hms = CLOCK_HMS_RE.fullmatch(value)
    if hms:
        hours, minutes, seconds = (int(hms.group(key)) for key in ("h", "m", "s"))
        if hours < 24 and minutes < 60 and seconds < 60:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return None

    twelve = CLOCK_12H_RE.fullmatch(value)
    if twelve:
        hours = int(twelve.group("h"))
        minutes = int(twelve.group("m"))
        seconds = int(twelve.group("s") or 0)
        if not (1 <= hours <= 12 and minutes < 60 and seconds < 60):
            return None
        meridiem = twelve.group("ampm").upper()
        if meridiem == "AM":
            hours = 0 if hours == 12 else hours
        elif hours != 12:
            hours += 12
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    hm = CLOCK_HM_RE.fullmatch(value)
    if hm:
        hours, minutes = int(hm.group("h")), int(hm.group("m"))
        if hours < 24 and minutes < 60:
            return f"{hours:02d}:{minutes:02d}:00"
        return None

    return None


def normalize_speaker(raw: str) -> str:
    name = raw.rstrip(":").strip()
    return ROLE_SPLIT_RE.split(name, maxsplit=1)[0].strip()


def sequential_timestamp(index: int, step_seconds: int = 5) -> str:
    total = max(0, index * step_seconds)
    hours, remainder = divmod(total, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def finalize_segments(
    segments: list[TranscriptSegmentCreate],
) -> list[TranscriptSegmentCreate]:
    for index, segment in enumerate(segments):
        segment.sequence_number = index
    for index in range(len(segments) - 1):
        segments[index].end_time = segments[index + 1].start_time
    return segments


def turns_to_segments(turns: list[TranscriptTurnOutput]) -> list[TranscriptSegmentCreate]:
    segments: list[TranscriptSegmentCreate] = []
    for index, turn in enumerate(turns):
        text = turn.text.strip()
        speaker = normalize_speaker(turn.speaker) or "Speaker"
        if not text:
            continue
        timestamp = normalize_timestamp(turn.timestamp or "") if turn.timestamp else None
        segments.append(
            TranscriptSegmentCreate(
                speaker=speaker,
                start_time=timestamp or sequential_timestamp(index),
                text=text,
                sequence_number=index,
            )
        )
    return finalize_segments(segments)


class TranscriptParser:
    def try_parse(self, raw_text: str) -> list[TranscriptSegmentCreate]:
        text = raw_text.strip()
        if not text:
            return []

        timed = self._parse_timed(text)
        if timed:
            return timed
        return self._parse_named_turns(text)

    def parse(self, raw_text: str) -> list[TranscriptSegmentCreate]:
        text = raw_text.strip()
        if not text:
            raise InvalidTranscriptError("Transcript is empty.")

        segments = self.try_parse(raw_text)
        if not segments:
            raise InvalidTranscriptError(
                "Could not parse a labelled transcript. "
                "Smart Meet will try to read free-form notes with the model."
            )
        return segments

    def _parse_timed(self, text: str) -> list[TranscriptSegmentCreate]:
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
            stripped = line.strip()
            header = self._match_timed_header(stripped)
            if header:
                flush()
                current_time, current_speaker, body = header
                current_lines = [body] if body else []
            elif current_speaker is not None:
                current_lines.append(line)

        flush()
        return finalize_segments(segments)

    def _match_timed_header(self, stripped: str) -> tuple[str, str, str] | None:
        match = HEADER_RE.match(stripped)
        if match:
            timestamp = normalize_timestamp(match.group("clock"))
            speaker = normalize_speaker(match.group("speaker"))
            if timestamp and speaker:
                return timestamp, speaker, match.group("body").strip()

        match = ZOOM_RE.match(stripped)
        if match:
            timestamp = normalize_timestamp(match.group("clock"))
            speaker = normalize_speaker(match.group("speaker"))
            if timestamp and speaker:
                return timestamp, speaker, match.group("body").strip()

        return None

    def _parse_named_turns(self, text: str) -> list[TranscriptSegmentCreate]:
        segments: list[TranscriptSegmentCreate] = []
        current_speaker: str | None = None
        current_lines: list[str] = []

        def flush() -> None:
            nonlocal current_speaker, current_lines
            if current_speaker:
                content = "\n".join(current_lines).strip()
                if content:
                    segments.append(
                        TranscriptSegmentCreate(
                            speaker=current_speaker,
                            start_time=sequential_timestamp(len(segments)),
                            text=content,
                            sequence_number=len(segments),
                        )
                    )
            current_lines = []

        for line in text.splitlines():
            stripped = line.strip()
            match = NAME_TURN_RE.match(stripped)
            if match:
                flush()
                current_speaker = normalize_speaker(match.group("speaker"))
                current_lines = [match.group("body").strip()] if match.group("body").strip() else []
            elif current_speaker is not None:
                current_lines.append(line)

        flush()
        return finalize_segments(segments) if len(segments) >= 2 else []
