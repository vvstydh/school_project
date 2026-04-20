import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

_SUBJECT_RE = r"^[А-ЯЁа-яё][А-ЯЁа-яё\s\-]+$"


class SubjectCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, pattern=_SUBJECT_RE)


class SubjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=100, pattern=_SUBJECT_RE)


class SubjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:         uuid.UUID
    name:       str
    created_at: datetime
    updated_at: datetime
