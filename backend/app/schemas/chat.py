from pydantic import BaseModel, Field


class ChatHistoryMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=8000)


class AskMeetingRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    history: list[ChatHistoryMessage] = Field(default_factory=list)


class SourceCitation(BaseModel):
    segmentId: str
    speaker: str
    timestamp: str
    text: str
    score: float | None = None


class AskMeetingResponse(BaseModel):
    answer: str
    sources: list[SourceCitation]
