import asyncio
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Request, Response, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import MeetingNotFoundError, MeetingNotReadyError
from app.llm.client import LLMClient
from app.models.meeting import MeetingStatus
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.meeting_repository import MeetingRepository
from app.schemas.chat import AskMeetingRequest, AskMeetingResponse, SourceCitation
from app.schemas.meeting import (
    ActionItemResponse,
    DecisionResponse,
    MeetingDetailResponse,
    MeetingListItem,
    MeetingUploadResponse,
    RiskResponse,
    TranscriptSegmentResponse,
)
from app.services.embedding_service import EmbeddingService
from app.services.guardrails import (
    classify_upload,
    question_limiter,
    upload_limiter,
    validate_audio_upload,
    validate_question,
    validate_upload,
)
from app.services.meeting_processing_service import MeetingProcessingService
from app.services.rag_service import RagService
from app.services.retrieval_service import RetrievalService
from app.services.transcription_service import TranscriptionService

router = APIRouter(prefix="/meetings", tags=["meetings"])


def _source(segment) -> SourceCitation | None:
    if segment is None:
        return None
    return SourceCitation(
        segmentId=segment.id,
        speaker=segment.speaker,
        timestamp=segment.start_time,
        text=segment.text,
    )


@router.get("", response_model=list[MeetingListItem])
async def list_meetings(db: AsyncSession = Depends(get_db)):
    meetings = await MeetingRepository(db).list()

    return [
        MeetingListItem(
            id=meeting.id,
            title=meeting.title,
            status=meeting.status,
            createdAt=meeting.created_at,
            participantCount=len({item.speaker for item in meeting.transcript_segments}),
            decisionCount=len(meeting.decisions),
            actionItemCount=len(meeting.action_items),
        )
        for meeting in meetings
    ]


@router.post("", response_model=MeetingUploadResponse)
async def create_meeting(
    request: Request,
    title: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    client = request.client.host if request.client else "unknown"
    upload_limiter.hit(f"upload:{client}")
    content = await file.read()
    filename = file.filename or ""
    if not Path(filename).suffix:
        filename = (
            "recording.webm"
            if (file.content_type or "").startswith("audio/")
            else "transcript.txt"
        )
    kind = classify_upload(filename)

    if kind == "audio":
        validate_audio_upload(filename, content)
        raw_text = await asyncio.to_thread(
            TranscriptionService().transcribe,
            content,
            filename,
        )
    else:
        raw_text = validate_upload(filename, content)

    repository = MeetingRepository(db)
    meeting = await repository.create(title.strip() or "Untitled meeting")
    await MeetingProcessingService(db).process(meeting, raw_text)
    await db.commit()

    return MeetingUploadResponse(id=meeting.id, title=meeting.title, status=meeting.status)


@router.get("/{meeting_id}", response_model=MeetingDetailResponse)
async def get_meeting(meeting_id: str, db: AsyncSession = Depends(get_db)):
    meeting = await MeetingRepository(db).get(meeting_id)
    if meeting is None:
        raise MeetingNotFoundError("Meeting not found")

    segments_by_id = {segment.id: segment for segment in meeting.transcript_segments}
    transcript = sorted(meeting.transcript_segments, key=lambda item: item.sequence_number)
    participants = list(dict.fromkeys(item.speaker for item in transcript))

    return MeetingDetailResponse(
        id=meeting.id,
        title=meeting.title,
        status=meeting.status,
        createdAt=meeting.created_at,
        participants=participants,
        summary=meeting.summary or "",
        transcript=[
            TranscriptSegmentResponse(
                id=item.id,
                speaker=item.speaker,
                startTime=item.start_time,
                endTime=item.end_time,
                text=item.text,
            )
            for item in transcript
        ],
        decisions=[
            DecisionResponse(
                id=item.id,
                text=item.text,
                source=_source(segments_by_id.get(item.source_segment_id)),
            )
            for item in meeting.decisions
        ],
        actionItems=[
            ActionItemResponse(
                id=item.id,
                task=item.task,
                owner=item.owner,
                dueDate=item.due_date,
                source=_source(segments_by_id.get(item.source_segment_id)),
            )
            for item in meeting.action_items
        ],
        risks=[
            RiskResponse(
                id=item.id,
                text=item.text,
                source=_source(segments_by_id.get(item.source_segment_id)),
            )
            for item in meeting.risks
        ],
    )


@router.post("/{meeting_id}/chat", response_model=AskMeetingResponse)
async def ask_meeting(
    meeting_id: str,
    payload: AskMeetingRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    client = request.client.host if request.client else "unknown"
    question_limiter.hit(f"question:{client}:{meeting_id}")
    question = validate_question(payload.question)

    meeting = await MeetingRepository(db).get(meeting_id)
    if meeting is None:
        raise MeetingNotFoundError("Meeting not found")
    if meeting.status != MeetingStatus.READY:
        raise MeetingNotReadyError("Meeting is not ready for questions yet.")

    chunk_repository = ChunkRepository(db)
    embedding_service = EmbeddingService()
    retrieval_service = RetrievalService(chunk_repository, embedding_service)
    rag_service = RagService(db, retrieval_service, LLMClient())

    return await rag_service.answer(meeting, question, payload.history)


@router.delete("/{meeting_id}", status_code=204)
async def delete_meeting(meeting_id: str, db: AsyncSession = Depends(get_db)):
    deleted = await MeetingRepository(db).delete(meeting_id)
    if not deleted:
        raise MeetingNotFoundError("Meeting not found")
    await db.commit()
    return Response(status_code=204)
