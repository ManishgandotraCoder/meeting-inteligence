from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidTranscriptError
from app.core.logging import logger
from app.llm.client import LLMClient
from app.models.meeting import Meeting, MeetingStatus
from app.repositories.chunk_repository import ChunkCreate, ChunkRepository
from app.repositories.insight_repository import InsightRepository
from app.repositories.meeting_repository import MeetingRepository
from app.repositories.transcript_repository import TranscriptRepository
from app.services.ai_transcript_parser import AiTranscriptParser
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.meeting_analysis_service import MeetingAnalysisService
from app.services.transcript_parser import TranscriptParser


class MeetingProcessingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.meetings = MeetingRepository(db)
        self.transcripts = TranscriptRepository(db)
        self.chunks = ChunkRepository(db)
        self.insights = InsightRepository(db)
        self.parser = TranscriptParser()
        self.ai_parser = AiTranscriptParser()
        self.chunker = ChunkingService()
        self.embeddings = EmbeddingService()
        self.analysis = MeetingAnalysisService(LLMClient())

    async def process(self, meeting: Meeting, raw_text: str) -> None:
        await self.meetings.update_status(meeting, MeetingStatus.PROCESSING)

        try:
            parsed = self.parser.try_parse(raw_text)
            parse_mode = "heuristic"
            if not parsed:
                parse_mode = "llm"
                parsed = await self.ai_parser.parse(raw_text)
            if not parsed:
                raise InvalidTranscriptError(
                    "Could not find meeting discussion in this file."
                )

            segments = await self.transcripts.bulk_create(meeting.id, parsed)

            transcript_chunks = self.chunker.chunk(segments, meeting_id=meeting.id)
            vectors = await self.embeddings.embed_many(
                [chunk.content for chunk in transcript_chunks]
            )

            await self.chunks.bulk_create(
                meeting.id,
                [
                    ChunkCreate(
                        content=chunk.content,
                        embedding=vector,
                        start_time=chunk.start_time,
                        end_time=chunk.end_time,
                        speakers=chunk.speakers,
                        segment_ids=chunk.segment_ids,
                    )
                    for chunk, vector in zip(transcript_chunks, vectors, strict=True)
                ],
            )

            analysis = await self.analysis.analyze(segments)
            meeting.summary = analysis.summary
            await self.insights.replace(meeting.id, analysis)
            await self.meetings.update_status(meeting, MeetingStatus.READY)

            logger.info(
                "meeting_processing_complete",
                meeting_id=meeting.id,
                parse_mode=parse_mode,
                segments=len(segments),
                chunks=len(transcript_chunks),
                chunk_tokens=[chunk.token_count for chunk in transcript_chunks],
            )

        except Exception:
            await self.meetings.update_status(meeting, MeetingStatus.FAILED)
            raise
