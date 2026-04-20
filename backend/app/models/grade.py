import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, SmallInteger, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Grade(Base):
    __tablename__ = "grades"

    id:         Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lesson_id:  Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    value:      Mapped[int]        = mapped_column(SmallInteger, nullable=False)
    comment:    Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime]   = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime]   = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("lesson_id", "student_id", name="uq_grades_lesson_student"),)

    lesson:  Mapped["Lesson"] = relationship("Lesson", back_populates="grades", lazy="selectin")
    student: Mapped["User"]   = relationship("User", lazy="selectin", foreign_keys=[student_id])
