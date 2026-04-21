import re
import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

_CLASS_NAME_RE = re.compile(r'^[1-9][0-9]?[А-ЯЁ]$')


def _check_class_name(v: str | None) -> str | None:
    if v is not None and not _CLASS_NAME_RE.match(v):
        raise ValueError('Формат: номер от 1 до 99 и заглавная буква (например: 1А, 10Б)')
    return v


# ── Класс ─────────────────────────────────────────────────────────────────────

class ClassCreate(BaseModel):
    name:              str       = Field(..., min_length=2, max_length=4)
    academic_year:     int       = Field(..., ge=2000, le=2100)
    vice_principal_id: uuid.UUID | None = None

    @field_validator('name', mode='after')
    @classmethod
    def validate_name(cls, v: str) -> str:
        return _check_class_name(v)


class ClassUpdate(BaseModel):
    name:              str | None       = Field(None, min_length=2, max_length=4)
    academic_year:     int | None       = Field(None, ge=2000, le=2100)
    vice_principal_id: uuid.UUID | None = None

    @field_validator('name', mode='after')
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        return _check_class_name(v)


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
