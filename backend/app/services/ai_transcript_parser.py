from app.core.exceptions import AIProviderError, InvalidTranscriptError
from app.core.logging import logger
from app.core.tokens import estimate_tokens
from app.llm.client import LLMClient
from app.llm.prompts import PARSE_SYSTEM_PROMPT
from app.schemas.transcript import TranscriptSegmentCreate, TranscriptTurnOutput
from app.services.transcript_parser import turns_to_segments

PARSE_WINDOW_CHARS = 9000


def split_parse_windows(text: str, size: int = PARSE_WINDOW_CHARS) -> list[str]:
    stripped = text.strip()
    if len(stripped) <= size:
        return [stripped]

    windows: list[str] = []
    start = 0
    while start < len(stripped):
        end = min(len(stripped), start + size)
        if end < len(stripped):
            cut = stripped.rfind("\n", start + size // 2, end)
            if cut > start:
                end = cut
        chunk = stripped[start:end].strip()
        if chunk:
            windows.append(chunk)
        start = end
    return windows


class AiTranscriptParser:
    def __init__(self, llm_client: LLMClient | None = None):
        self.llm_client = llm_client or LLMClient()

    async def parse(self, raw_text: str) -> list[TranscriptSegmentCreate]:
        text = raw_text.strip()
        if not text:
            raise InvalidTranscriptError("Transcript is empty.")

        turns: list[TranscriptTurnOutput] = []
        windows = split_parse_windows(text)
        for index, window in enumerate(windows):
            extracted = await self._extract_window(window, index, len(windows))
            turns.extend(extracted)

        segments = turns_to_segments(turns)
        if not segments:
            raise InvalidTranscriptError(
                "Could not find meeting discussion in this file. "
                "Try a transcript, chat export, or notes with speakers."
            )
        return segments

    async def _extract_window(
        self, window: str, index: int, total: int
    ) -> list[TranscriptTurnOutput]:
        part = f" (part {index + 1} of {total})" if total > 1 else ""
        prompt = (
            f"Extract speaker turns from this meeting file{part}.\n\n"
            "<untrusted_transcript>\n"
            f"{window}\n"
            "</untrusted_transcript>"
        )
        try:
            result = await self.llm_client.extract_transcript(PARSE_SYSTEM_PROMPT, prompt)
        except AIProviderError:
            logger.info(
                "transcript_llm_parse_failed",
                window_index=index,
                window_tokens=estimate_tokens(window),
            )
            raise

        return result.segments
