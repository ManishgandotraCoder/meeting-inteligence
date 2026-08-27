from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class MeetingStatus(StrEnum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=MeetingStatus.UPLOADED)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    transcript_segments = relationship("TranscriptSegment", cascade="all, delete-orphan")
    chunks = relationship("DocumentChunk", cascade="all, delete-orphan")
    decisions = relationship("Decision", cascade="all, delete-orphan")
    action_items = relationship("ActionItem", cascade="all, delete-orphan")
    risks = relationship("Risk", cascade="all, delete-orphan")
