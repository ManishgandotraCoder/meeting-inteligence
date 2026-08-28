from pydantic import BaseModel, Field


class TranscriptSegmentCreate(BaseModel):
    speaker: str
    start_time: str
    end_time: str | None = None
    text: str
    sequence_number: int


class TranscriptSegmentResponse(BaseModel):
    id: str
    speaker: str
    startTime: str
    endTime: str | None = None
    text: str


class TranscriptTurnOutput(BaseModel):
    speaker: str = Field(min_length=1, max_length=120)
    timestamp: str | None = None
    text: str = Field(min_length=1)


class TranscriptParseOutput(BaseModel):
    segments: list[TranscriptTurnOutput] = Field(default_factory=list)
