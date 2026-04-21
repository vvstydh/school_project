import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

_CLASS_NAME_RE = r"^[1-9][0-9]?[А-ЯЁ]$"


# ── Класс ─────────────────────────────────────────────────────────────────────

class ClassCreate(BaseModel):
    name:              str       = Field(..., pattern=_CLASS_NAME_RE)
    academic_year:     int       = Field(..., ge=2000, le=2100)
    vice_principal_id: uuid.UUID | None = None


class ClassUpdate(BaseModel):
    name:              str | None       = Field(None, pattern=_CLASS_NAME_RE)
    academic_year:     int | None       = Field(None, ge=2000, le=2100)
    vice_principal_id: uuid.UUID | None = None


class ClassResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:                uuid.UUID
    name:              str
    academic_year:     int
    vice_principal_id: uuid.UUID | None
    created_at:        datetime
    updated_at:        datetime


# ── Ученик в классе ───────────────────────────────────────────────────────────

class ClassStudentCreate(BaseModel):
    class_id:      uuid.UUID
    student_id:    uuid.UUID
    academic_year: int  = Field(..., ge=2000, le=2100)
    enrolled_at:   date | None = None


class StudentShort(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:         uuid.UUID
    first_name: str
    last_name:  str
    email:      str


class ClassStudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:            uuid.UUID
    class_id:      uuid.UUID
    student_id:    uuid.UUID
    academic_year: int
    enrolled_at:   date
    student:       StudentShort | None = None


# ── Учитель в классе ──────────────────────────────────────────────────────────

class TeacherClassCreate(BaseModel):
    teacher_id: uuid.UUID
    class_id:   uuid.UUID


class TeacherClassResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:         uuid.UUID
    teacher_id: uuid.UUID
    class_id:   uuid.UUID
    created_at: datetime


# ── Связь родитель–ребёнок ────────────────────────────────────────────────────

class ParentStudentCreate(BaseModel):
    parent_id:  uuid.UUID
    student_id: uuid.UUID


class ParentStudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    parent_id:  uuid.UUID
    student_id: uuid.UUID
