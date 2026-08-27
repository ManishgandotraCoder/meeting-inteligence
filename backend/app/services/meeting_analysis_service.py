from app.llm.client import LLMClient
from app.llm.prompts import ANALYSIS_SYSTEM_PROMPT
from app.models.transcript import TranscriptSegment
from app.schemas.insights import MeetingAnalysisOutput


class MeetingAnalysisService:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    async def analyze(self, segments: list[TranscriptSegment]) -> MeetingAnalysisOutput:
        transcript = "\n\n".join(
            f'<segment id="{segment.id}">\n'
            f"[{segment.start_time}] {segment.speaker}:\n"
            f"{segment.text}\n"
            f"</segment>"
            for segment in segments
        )

        prompt = f"""
Extract a concise meeting summary, decisions, action items, and risks.

A decision is an agreed or confirmed outcome.
An action item is work assigned or clearly committed to.
A suggestion is not automatically a decision.
Do not invent owners or deadlines. Use null when they are not mentioned.

<untrusted_transcript>
{transcript}
</untrusted_transcript>
""".strip()

        return await self.llm_client.analyze(ANALYSIS_SYSTEM_PROMPT, prompt)
