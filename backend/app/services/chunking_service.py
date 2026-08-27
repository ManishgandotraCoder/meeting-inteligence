from dataclasses import dataclass

from app.core.config import settings
from app.core.tokens import estimate_tokens
from app.models.transcript import TranscriptSegment


@dataclass(slots=True)
class TranscriptChunk:
    meeting_id: str
    chunk_index: int
    content: str
    start_time: str | None
    end_time: str | None
    speakers: list[str]
    segment_ids: list[str]
    token_count: int


class ChunkingService:
    def __init__(
        self,
        target_tokens: int | None = None,
        max_tokens: int | None = None,
        overlap_tokens: int | None = None,
        short_transcript_tokens: int | None = None,
    ):
        self.target_tokens = target_tokens or settings.chunk_target_tokens
        self.max_tokens = max_tokens or settings.chunk_max_tokens
        self.overlap_tokens = overlap_tokens or settings.chunk_overlap_tokens
        self.short_transcript_tokens = (
            short_transcript_tokens or settings.short_transcript_tokens
        )

    def _format(self, segment: TranscriptSegment) -> str:
        return f"[{segment.start_time}] {segment.speaker}:\n{segment.text.strip()}"

    def _tokens(self, value: str) -> int:
        return estimate_tokens(value)

    def _make_chunk(
        self,
        meeting_id: str,
        chunk_index: int,
        selected: list[TranscriptSegment],
    ) -> TranscriptChunk:
        content = "\n\n".join(self._format(item) for item in selected)
        return TranscriptChunk(
            meeting_id=meeting_id,
            chunk_index=chunk_index,
            content=content,
            start_time=selected[0].start_time,
            end_time=selected[-1].end_time or selected[-1].start_time,
            speakers=list(dict.fromkeys(item.speaker for item in selected)),
            segment_ids=[item.id for item in selected],
            token_count=self._tokens(content),
        )

    def chunk(
        self,
        segments: list[TranscriptSegment],
        meeting_id: str = "",
    ) -> list[TranscriptChunk]:
        if not segments:
            return []

        formatted_tokens = [self._tokens(self._format(segment)) for segment in segments]
        total_tokens = sum(formatted_tokens)

        if total_tokens <= self.short_transcript_tokens:
            return [self._make_chunk(meeting_id, 0, segments)]

        chunks: list[TranscriptChunk] = []
        cursor = 0

        while cursor < len(segments):
            selected: list[TranscriptSegment] = []
            token_count = 0
            index = cursor

            while index < len(segments):
                candidate_tokens = formatted_tokens[index]
                would_exceed_max = selected and token_count + candidate_tokens > self.max_tokens
                if would_exceed_max:
                    break

                selected.append(segments[index])
                token_count += candidate_tokens
                index += 1

                if token_count >= self.target_tokens:
                    break

            if not selected:
                selected = [segments[cursor]]
                index = cursor + 1

            chunks.append(self._make_chunk(meeting_id, len(chunks), selected))

            overlap = 0
            next_cursor = index
            probe = index - 1
            while probe > cursor and overlap < self.overlap_tokens:
                overlap += formatted_tokens[probe]
                next_cursor = probe
                probe -= 1

            cursor = max(cursor + 1, next_cursor)

        return chunks
