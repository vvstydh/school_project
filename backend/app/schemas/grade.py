import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class GradeCreate(BaseModel):
    lesson_id:  uuid.UUID
    student_id: uuid.UUID
    value:      int      = Field(..., ge=1, le=5)
    comment:    str | None = Field(None, min_length=2, max_length=1000)


class GradeUpdate(BaseModel):
    value:   int | None = Field(None, ge=1, le=5)
    comment: str | None = Field(None, min_length=2, max_length=1000)


class GradeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:         uuid.UUID
    lesson_id:  uuid.UUID
    student_id: uuid.UUID
    value:      int
    comment:    str | None
    created_at: datetime
    updated_at: datetime
