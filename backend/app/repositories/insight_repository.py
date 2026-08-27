from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.insight import ActionItem, Decision, Risk
from app.schemas.insights import MeetingAnalysisOutput


class InsightRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def replace(
        self,
        meeting_id: str,
        analysis: MeetingAnalysisOutput,
    ) -> None:
        # MVP is write-once during processing. A production version should delete/replace
        # existing insight rows when reprocessing a meeting.
        self.db.add_all(
            [
                Decision(
                    id=str(uuid4()),
                    meeting_id=meeting_id,
                    text=item.text,
                    source_segment_id=item.source_segment_id,
                )
                for item in analysis.decisions
            ]
        )
        self.db.add_all(
            [
                ActionItem(
                    id=str(uuid4()),
                    meeting_id=meeting_id,
                    task=item.task,
                    owner=item.owner,
                    due_date=item.due_date,
                    source_segment_id=item.source_segment_id,
                )
                for item in analysis.action_items
            ]
        )
        self.db.add_all(
            [
                Risk(
                    id=str(uuid4()),
                    meeting_id=meeting_id,
                    text=item.text,
                    source_segment_id=item.source_segment_id,
                )
                for item in analysis.risks
            ]
        )
        await self.db.flush()
