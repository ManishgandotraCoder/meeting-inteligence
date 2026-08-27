from datetime import datetime

from pydantic import BaseModel

from app.schemas.chat import SourceCitation


class MeetingUploadResponse(BaseModel):
    id: str
    title: str
    status: str


class MeetingListItem(BaseModel):
    id: str
    title: str
    status: str
    createdAt: datetime
    participantCount: int
    decisionCount: int
    actionItemCount: int


class DecisionResponse(BaseModel):
    id: str
    text: str
    source: SourceCitation | None = None


class ActionItemResponse(BaseModel):
    id: str
    task: str
    owner: str | None = None
    dueDate: str | None = None
    source: SourceCitation | None = None


class RiskResponse(BaseModel):
    id: str
    text: str
    source: SourceCitation | None = None


class TranscriptSegmentResponse(BaseModel):
    id: str
    speaker: str
    startTime: str
    endTime: str | None = None
    text: str


class MeetingDetailResponse(BaseModel):
    id: str
    title: str
    status: str
    createdAt: datetime
    participants: list[str]
    summary: str
    transcript: list[TranscriptSegmentResponse]
    decisions: list[DecisionResponse]
    actionItems: list[ActionItemResponse]
    risks: list[RiskResponse]
