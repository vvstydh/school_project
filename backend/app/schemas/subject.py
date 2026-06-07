import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

_SUBJECT_RE = re.compile(r'^[А-ЯЁ][А-ЯЁа-яё\s\-]+$')


def _check_subject_name(v: str | None) -> str | None:
    if v is not None and not _SUBJECT_RE.match(v):
        raise ValueError('Название должно начинаться с заглавной русской буквы и содержать только кириллицу, пробел или дефис')
    return v


class SubjectCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)

    @field_validator('name', mode='after')
    @classmethod
    def validate_name(cls, v: str) -> str:
        return _check_subject_name(v)


class SubjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=100)

    @field_validator('name', mode='after')
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        return _check_subject_name(v)


class SubjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:         uuid.UUID
    name:       str
    created_at: datetime
    updated_at: datetime
