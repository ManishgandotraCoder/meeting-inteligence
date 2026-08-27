from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transcript import TranscriptSegment
from app.schemas.transcript import TranscriptSegmentCreate


class TranscriptRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def bulk_create(
        self,
        meeting_id: str,
        segments: list[TranscriptSegmentCreate],
    ) -> list[TranscriptSegment]:
        rows = [
            TranscriptSegment(
                id=str(uuid4()),
                meeting_id=meeting_id,
                speaker=item.speaker,
                start_time=item.start_time,
                end_time=item.end_time,
                text=item.text,
                sequence_number=item.sequence_number,
            )
            for item in segments
        ]
        self.db.add_all(rows)
        await self.db.flush()
        return rows
