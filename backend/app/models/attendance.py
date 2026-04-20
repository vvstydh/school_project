import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Attendance(Base):
    __tablename__ = "attendances"

    id:         Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lesson_id:  Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status:     Mapped[str]       = mapped_column(
        SAEnum("present", "absent", "late", "excused", name="attendance_status", create_type=False),
        nullable=False,
        default="present",
    )
    created_at: Mapped[datetime]  = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime]  = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("lesson_id", "student_id", name="uq_attendances_lesson_student"),)

    lesson:  Mapped["Lesson"] = relationship("Lesson", back_populates="attendances", lazy="selectin")
    student: Mapped["User"]   = relationship("User", lazy="selectin", foreign_keys=[student_id])
