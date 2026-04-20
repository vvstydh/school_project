import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, SmallInteger, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Class(Base):
    __tablename__ = "classes"

    id:                Mapped[uuid.UUID]       = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name:              Mapped[str]             = mapped_column(String(10), nullable=False)
    academic_year:     Mapped[int]             = mapped_column(SmallInteger, nullable=False)
    vice_principal_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at:        Mapped[datetime]        = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:        Mapped[datetime]        = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("name", "academic_year", name="uq_classes_name_year"),)

    vice_principal: Mapped["User | None"] = relationship(
        "User", back_populates="managed_classes", foreign_keys=[vice_principal_id], lazy="selectin",
    )
    class_students: Mapped[list["ClassStudent"]] = relationship(
        "ClassStudent", back_populates="class_", lazy="selectin",
    )
    teacher_classes: Mapped[list["TeacherClass"]] = relationship(
        "TeacherClass", back_populates="class_", lazy="selectin",
    )
    lessons: Mapped[list["Lesson"]] = relationship(
        "Lesson", back_populates="class_", lazy="selectin",
    )


class ClassStudent(Base):
    __tablename__ = "class_students"

    id:            Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_id:      Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("classes.id", ondelete="CASCADE"), nullable=False)
    student_id:    Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    academic_year: Mapped[int]       = mapped_column(SmallInteger, nullable=False)
    enrolled_at:   Mapped[date]      = mapped_column(Date, nullable=False, server_default=func.current_date())

    __table_args__ = (UniqueConstraint("student_id", "academic_year", name="uq_class_students_student_year"),)

    class_:  Mapped["Class"] = relationship("Class", back_populates="class_students", lazy="selectin")
    student: Mapped["User"]  = relationship("User", lazy="selectin", foreign_keys=[student_id])


class TeacherClass(Base):
    __tablename__ = "teacher_classes"

    id:         Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    teacher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    class_id:   Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("classes.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime]  = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("teacher_id", "class_id", name="uq_teacher_classes"),)

    teacher: Mapped["User"]  = relationship("User", lazy="selectin", foreign_keys=[teacher_id])
    class_:  Mapped["Class"] = relationship("Class", back_populates="teacher_classes", lazy="selectin")
