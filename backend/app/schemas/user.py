import re
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


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
    date_of_birth: str | None = None
    record_number: str | None = Field(None, min_length=1, max_length=50)

    @field_validator('date_of_birth', mode='after')
    @classmethod
    def validate_dob(cls, v: str | None) -> str | None:
        if v is not None and not re.match(r'^\d{4}-\d{2}-\d{2}$', v):
            raise ValueError('Введите дату в формате ГГГГ-ММ-ДД')
        return v


class StudentProfileUpdate(BaseModel):
    date_of_birth: str | None = None
    record_number: str | None = Field(None, min_length=1, max_length=50)

    @field_validator('date_of_birth', mode='after')
    @classmethod
    def validate_dob(cls, v: str | None) -> str | None:
        if v is not None and not re.match(r'^\d{4}-\d{2}-\d{2}$', v):
            raise ValueError('Введите дату в формате ГГГГ-ММ-ДД')
        return v


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

_NAME_RE    = re.compile(r'^[А-ЯЁ][а-яё\-]+$')
_MIDNAME_RE = re.compile(r'^[А-ЯЁ][а-яё]+$')


def _check_name(v: str | None) -> str | None:
    if v is not None and not _NAME_RE.match(v):
        raise ValueError('Должно начинаться с заглавной русской буквы и содержать только строчные русские буквы')
    return v


def _check_midname(v: str | None) -> str | None:
    if v is not None and not _MIDNAME_RE.match(v):
        raise ValueError('Должно начинаться с заглавной русской буквы и содержать только строчные русские буквы (без дефиса)')
    return v


class UserCreate(BaseModel):
    email:       EmailStr
    password:    str      = Field(..., min_length=8, max_length=128)
    role:        RoleType
    first_name:  str      = Field(..., min_length=2, max_length=100)
    last_name:   str      = Field(..., min_length=2, max_length=100)
    middle_name: str | None = Field(None, min_length=2, max_length=100)

    @field_validator('first_name', 'last_name', mode='after')
    @classmethod
    def validate_name(cls, v: str) -> str:
        return _check_name(v)

    @field_validator('middle_name', mode='after')
    @classmethod
    def validate_middle_name(cls, v: str | None) -> str | None:
        return _check_midname(v)


class UserUpdate(BaseModel):
    email:       EmailStr | None = None
    password:    str | None      = Field(None, min_length=8, max_length=128)
    role:        RoleType | None = None
    first_name:  str | None      = Field(None, min_length=2, max_length=100)
    last_name:   str | None      = Field(None, min_length=2, max_length=100)
    middle_name: str | None      = Field(None, min_length=2, max_length=100)
    is_active:   bool | None     = None

    @field_validator('first_name', 'last_name', mode='after')
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        return _check_name(v)

    @field_validator('middle_name', mode='after')
    @classmethod
    def validate_middle_name(cls, v: str | None) -> str | None:
        return _check_midname(v)


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
    children:        list[UserShort] = []
