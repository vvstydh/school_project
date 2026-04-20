import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum as SAEnum, ForeignKey, String, Table, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base

parent_student = Table(
    "parent_student",
    Base.metadata,
    Column("parent_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("student_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id:            Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email:         Mapped[str]        = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str]        = mapped_column(Text, nullable=False)
    role:          Mapped[str]        = mapped_column(
        SAEnum("admin", "vice_principal", "teacher", "student", "parent", name="user_role", create_type=False),
        nullable=False,
    )
    first_name:    Mapped[str]        = mapped_column(String(100), nullable=False)
    last_name:     Mapped[str]        = mapped_column(String(100), nullable=False)
    middle_name:   Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active:     Mapped[bool]       = mapped_column(Boolean, nullable=False, default=True)
    created_at:    Mapped[datetime]   = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:    Mapped[datetime]   = mapped_column(DateTime(timezone=True), server_default=func.now())

    teacher_profile: Mapped["TeacherProfile | None"] = relationship(
        "TeacherProfile", back_populates="user", uselist=False, lazy="selectin",
    )
    student_profile: Mapped["StudentProfile | None"] = relationship(
        "StudentProfile", back_populates="user", uselist=False, lazy="selectin",
    )
    managed_classes: Mapped[list["Class"]] = relationship(
        "Class", back_populates="vice_principal", foreign_keys="Class.vice_principal_id", lazy="selectin",
    )
    children: Mapped[list["User"]] = relationship(
        "User",
        secondary=parent_student,
        primaryjoin="User.id == parent_student.c.parent_id",
        secondaryjoin="User.id == parent_student.c.student_id",
        lazy="selectin",
        overlaps="parents",
    )
    parents: Mapped[list["User"]] = relationship(
        "User",
        secondary=parent_student,
        primaryjoin="User.id == parent_student.c.student_id",
        secondaryjoin="User.id == parent_student.c.parent_id",
        lazy="selectin",
        overlaps="children",
    )


class TeacherProfile(Base):
    __tablename__ = "teacher_profiles"

    id:         Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id:    Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    subject_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[datetime]  = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime]  = mapped_column(DateTime(timezone=True), server_default=func.now())

    user:    Mapped["User"]    = relationship("User", back_populates="teacher_profile")
    subject: Mapped["Subject"] = relationship("Subject", back_populates="teacher_profiles", lazy="selectin")


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id:            Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id:       Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    date_of_birth: Mapped[str | None] = mapped_column(nullable=True)
    record_number: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    created_at:    Mapped[datetime]   = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:    Mapped[datetime]   = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="student_profile")
