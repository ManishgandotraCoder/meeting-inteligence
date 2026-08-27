from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.meeting import Meeting, MeetingStatus


class MeetingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, title: str) -> Meeting:
        meeting = Meeting(id=str(uuid4()), title=title, status=MeetingStatus.UPLOADED)
        self.db.add(meeting)
        await self.db.flush()
        return meeting

    async def get(self, meeting_id: str) -> Meeting | None:
        stmt = (
            select(Meeting)
            .where(Meeting.id == meeting_id)
            .options(
                selectinload(Meeting.transcript_segments),
                selectinload(Meeting.decisions),
                selectinload(Meeting.action_items),
                selectinload(Meeting.risks),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self) -> list[Meeting]:
        stmt = (
            select(Meeting)
            .options(
                selectinload(Meeting.transcript_segments),
                selectinload(Meeting.decisions),
                selectinload(Meeting.action_items),
            )
            .order_by(Meeting.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().unique())

    async def update_status(self, meeting: Meeting, status: MeetingStatus) -> None:
        meeting.status = status
        await self.db.flush()

    async def delete(self, meeting_id: str) -> bool:
        result = await self.db.execute(delete(Meeting).where(Meeting.id == meeting_id))
        return (result.rowcount or 0) > 0
