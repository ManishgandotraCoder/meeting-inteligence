from pydantic import BaseModel


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
