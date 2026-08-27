import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.context import request_id_ctx, user_id_ctx
from app.core.logging import logger
from app.core.tokens import estimate_tokens
from app.llm.client import LLMClient
from app.llm.prompts import LOW_CONFIDENCE_FALLBACK, PROMPT_VERSION, RAG_SYSTEM_PROMPT
from app.models.meeting import Meeting
from app.models.transcript import TranscriptSegment
from app.repositories.chunk_repository import RetrievedChunk
from app.schemas.chat import AskMeetingResponse, ChatHistoryMessage, SourceCitation
from app.services.guardrails import filter_cited_chunks
from app.services.query_rewrite import QueryRewriteService
from app.services.question_router import classify_question
from app.services.retrieval_service import RetrievalService


class RagService:
    def __init__(
        self,
        db: AsyncSession,
        retrieval_service: RetrievalService,
        llm_client: LLMClient,
    ):
        self.db = db
        self.retrieval_service = retrieval_service
        self.llm_client = llm_client
        self.rewriter = QueryRewriteService(llm_client)

    async def answer(
        self,
        meeting: Meeting,
        question: str,
        history: list[ChatHistoryMessage] | None = None,
    ) -> AskMeetingResponse:
        started = time.perf_counter()
        history = history or []
        standalone = await self.rewriter.rewrite(question, history)
        kind = classify_question(standalone)

        retrieve_started = time.perf_counter()
        chunks = await self.retrieval_service.retrieve(meeting.id, standalone)
        retrieve_ms = int((time.perf_counter() - retrieve_started) * 1000)

        best_vector = max((chunk.vector_score for chunk in chunks), default=0.0)
        low_confidence = not chunks or best_vector < settings.rag_min_score

        if kind == "open" and low_confidence:
            logger.info(
                "rag_abstain",
                request_id=request_id_ctx.get(),
                meeting_id=meeting.id,
                user_id=user_id_ctx.get(),
                question_length=len(question),
                retrieval_empty=not chunks,
                best_vector_score=best_vector,
                prompt_version=PROMPT_VERSION,
                retrieval_latency_ms=retrieve_ms,
            )
            return AskMeetingResponse(answer=LOW_CONFIDENCE_FALLBACK, sources=[])

        evidence = self._build_evidence(meeting, kind, chunks, history)
        user_prompt = (
            f"{evidence}\n\nSTANDALONE QUESTION\n{standalone}\n\nORIGINAL QUESTION\n{question}"
        )

        try:
            result = await self.llm_client.answer(RAG_SYSTEM_PROMPT, user_prompt)
        except Exception:
            logger.info(
                "rag_validation_failure",
                request_id=request_id_ctx.get(),
                meeting_id=meeting.id,
                error_category="llm_output",
            )
            return AskMeetingResponse(answer=LOW_CONFIDENCE_FALLBACK, sources=[])

        cited_chunks = filter_cited_chunks(result.cited_chunk_ids, chunks)
        if not cited_chunks and chunks and not result.insufficient_evidence:
            cited_chunks = chunks[:2]

        if result.insufficient_evidence or (kind == "open" and low_confidence):
            answer = LOW_CONFIDENCE_FALLBACK
            sources: list[SourceCitation] = []
        else:
            answer = result.answer.strip() or LOW_CONFIDENCE_FALLBACK
            sources = await self._sources(cited_chunks)

        logger.info(
            "rag_complete",
            request_id=request_id_ctx.get(),
            meeting_id=meeting.id,
            user_id=user_id_ctx.get(),
            question_length=len(question),
            rewritten=standalone != question,
            question_kind=kind,
            embedding_model=settings.embedding_model,
            chat_model=settings.chat_model,
            retrieval_method="hybrid",
            retrieved_chunk_ids=[chunk.id for chunk in chunks],
            retrieved_scores=[chunk.score for chunk in chunks],
            cited_chunk_ids=[chunk.id for chunk in cited_chunks],
            prompt_version=PROMPT_VERSION,
            retrieval_latency_ms=retrieve_ms,
            total_latency_ms=int((time.perf_counter() - started) * 1000),
            low_confidence=low_confidence,
        )

        return AskMeetingResponse(answer=answer, sources=sources[:4])

    def _build_evidence(
        self,
        meeting: Meeting,
        kind: str,
        chunks: list[RetrievedChunk],
        history: list[ChatHistoryMessage],
    ) -> str:
        parts: list[str] = []

        if kind == "action_items" and meeting.action_items:
            items = "\n".join(
                f"- {item.task} (owner={item.owner or 'null'}, due={item.due_date or 'null'})"
                for item in meeting.action_items
            )
            parts.append(f"STRUCTURED ACTION ITEMS\n{items}")
        elif kind == "decisions" and meeting.decisions:
            items = "\n".join(f"- {item.text}" for item in meeting.decisions)
            parts.append(f"STRUCTURED DECISIONS\n{items}")
        elif kind == "risks" and meeting.risks:
            items = "\n".join(f"- {item.text}" for item in meeting.risks)
            parts.append(f"STRUCTURED RISKS\n{items}")

        chunk_blocks: list[str] = []
        used_tokens = estimate_tokens("\n".join(parts))
        for chunk in chunks:
            speakers = ", ".join(chunk.speakers)
            block = (
                f'<chunk id="{chunk.id}" start="{chunk.start_time}" end="{chunk.end_time}" '
                f'speakers="{speakers}">\n{chunk.content}\n</chunk>'
            )
            block_tokens = estimate_tokens(block)
            if used_tokens + block_tokens > settings.rag_max_context_tokens:
                break
            chunk_blocks.append(block)
            used_tokens += block_tokens

        if chunk_blocks:
            parts.append(
                "TRANSCRIPT EVIDENCE\n<untrusted_transcript>\n"
                + "\n\n".join(chunk_blocks)
                + "\n</untrusted_transcript>"
            )

        recent = history[-settings.rag_history_messages :]
        if recent:
            history_text = "\n".join(f"{item.role}: {item.content}" for item in recent)
            parts.append(f"RECENT CHAT HISTORY\n{history_text}")

        return "\n\n".join(parts)

    async def _sources(self, chunks: list[RetrievedChunk]) -> list[SourceCitation]:
        sources: list[SourceCitation] = []
        for chunk in chunks:
            if not chunk.segment_ids:
                if chunk.start_time:
                    sources.append(
                        SourceCitation(
                            segmentId=chunk.id,
                            speaker=", ".join(chunk.speakers) or "Unknown",
                            timestamp=chunk.start_time,
                            text=chunk.content[:280],
                            score=chunk.score,
                        )
                    )
                continue

            stmt = (
                select(TranscriptSegment)
                .where(TranscriptSegment.id.in_(chunk.segment_ids))
                .order_by(TranscriptSegment.sequence_number)
            )
            rows = list((await self.db.execute(stmt)).scalars())
            for segment in rows[:2]:
                sources.append(
                    SourceCitation(
                        segmentId=segment.id,
                        speaker=segment.speaker,
                        timestamp=segment.start_time,
                        text=segment.text,
                        score=chunk.score,
                    )
                )
        return sources
