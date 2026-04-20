import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Lesson(Base):
    __tablename__ = "lessons"

    id:         Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_id:   Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), ForeignKey("classes.id", ondelete="CASCADE"), nullable=False)
    teacher_id: Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    subject_id: Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="RESTRICT"), nullable=False)
    date:       Mapped[date]       = mapped_column(Date, nullable=False)
    topic:      Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime]   = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime]   = mapped_column(DateTime(timezone=True), server_default=func.now())

    class_:   Mapped["Class"]   = relationship("Class", back_populates="lessons", lazy="selectin")
    teacher:  Mapped["User"]    = relationship("User", lazy="selectin", foreign_keys=[teacher_id])
    subject:  Mapped["Subject"] = relationship("Subject", back_populates="lessons", lazy="selectin")
    grades:      Mapped[list["Grade"]]      = relationship("Grade", back_populates="lesson", lazy="selectin")
    attendances: Mapped[list["Attendance"]] = relationship("Attendance", back_populates="lesson", lazy="selectin")
