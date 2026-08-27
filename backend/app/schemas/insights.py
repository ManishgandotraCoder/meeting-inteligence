from pydantic import BaseModel, Field


class DecisionOutput(BaseModel):
    text: str
    source_segment_id: str | None = None


class ActionItemOutput(BaseModel):
    task: str
    owner: str | None = None
    due_date: str | None = None
    source_segment_id: str | None = None


class RiskOutput(BaseModel):
    text: str
    source_segment_id: str | None = None


class MeetingAnalysisOutput(BaseModel):
    summary: str
    decisions: list[DecisionOutput] = Field(default_factory=list)
    action_items: list[ActionItemOutput] = Field(default_factory=list)
    risks: list[RiskOutput] = Field(default_factory=list)


class RagAnswerOutput(BaseModel):
    answer: str
    cited_chunk_ids: list[str] = Field(default_factory=list)
    insufficient_evidence: bool = False
