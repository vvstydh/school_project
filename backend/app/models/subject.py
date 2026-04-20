import uuid
from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Subject(Base):
    __tablename__ = "subjects"

    id:         Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name:       Mapped[str]       = mapped_column(String(100), unique=True, nullable=False)
    created_at: Mapped[datetime]  = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime]  = mapped_column(DateTime(timezone=True), server_default=func.now())

    teacher_profiles: Mapped[list["TeacherProfile"]] = relationship(
        "TeacherProfile", back_populates="subject", lazy="selectin",
    )
    lessons: Mapped[list["Lesson"]] = relationship(
        "Lesson", back_populates="subject", lazy="selectin",
    )
