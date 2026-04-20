import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ── Вспомогательная схема для вложенных ответов ───────────────────────────────

class UserShort(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:          uuid.UUID
    first_name:  str
    last_name:   str
    middle_name: str | None
    role:        str


# ── Профиль учителя ───────────────────────────────────────────────────────────

class TeacherProfileCreate(BaseModel):
    subject_id: uuid.UUID


class TeacherProfileUpdate(BaseModel):
    subject_id: uuid.UUID | None = None


class TeacherProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:         uuid.UUID
    user_id:    uuid.UUID
    subject_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ── Профиль ученика ───────────────────────────────────────────────────────────

class StudentProfileCreate(BaseModel):
    date_of_birth: str | None = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    record_number: str | None = Field(None, min_length=1, max_length=50)


class StudentProfileUpdate(BaseModel):
    date_of_birth: str | None = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    record_number: str | None = Field(None, min_length=1, max_length=50)


class StudentProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:            uuid.UUID
    user_id:       uuid.UUID
    date_of_birth: str | None
    record_number: str | None
    created_at:    datetime
    updated_at:    datetime


# ── Пользователь ──────────────────────────────────────────────────────────────

RoleType = Literal["admin", "vice_principal", "teacher", "student", "parent"]

_NAME_RE    = r"^[А-ЯЁ][а-яё\-]+$"
_MIDNAME_RE = r"^[А-ЯЁ][а-яё]+$"


class UserCreate(BaseModel):
    email:       EmailStr
    password:    str      = Field(..., min_length=8, max_length=128)
    role:        RoleType
    first_name:  str      = Field(..., min_length=2, max_length=100, pattern=_NAME_RE)
    last_name:   str      = Field(..., min_length=2, max_length=100, pattern=_NAME_RE)
    middle_name: str | None = Field(None, min_length=2, max_length=100, pattern=_MIDNAME_RE)


class UserUpdate(BaseModel):
    email:       EmailStr | None = None
    password:    str | None      = Field(None, min_length=8, max_length=128)
    first_name:  str | None      = Field(None, min_length=2, max_length=100, pattern=_NAME_RE)
    last_name:   str | None      = Field(None, min_length=2, max_length=100, pattern=_NAME_RE)
    middle_name: str | None      = Field(None, min_length=2, max_length=100, pattern=_MIDNAME_RE)
    is_active:   bool | None     = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:              uuid.UUID
    email:           str
    role:            str
    first_name:      str
    last_name:       str
    middle_name:     str | None
    is_active:       bool
    created_at:      datetime
    updated_at:      datetime
    teacher_profile: TeacherProfileResponse | None = None
    student_profile: StudentProfileResponse | None = None
