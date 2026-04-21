import uuid
from datetime import date as Date
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

_TOPIC_RE = r"^[А-ЯЁа-яё].*"


class LessonCreate(BaseModel):
    class_id:   uuid.UUID
    teacher_id: uuid.UUID
    subject_id: uuid.UUID
    date:       Date
    topic:      str | None = Field(None, min_length=2, max_length=500, pattern=_TOPIC_RE)


class LessonUpdate(BaseModel):
    date:  Date | None = None
    topic: str | None  = Field(None, min_length=2, max_length=500, pattern=_TOPIC_RE)


class LessonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:           uuid.UUID
    class_id:     uuid.UUID
    teacher_id:   uuid.UUID
    subject_id:   uuid.UUID
    date:         Date
    topic:        str | None
    created_at:   datetime
    updated_at:   datetime
    subject_name: str | None = None
    class_name:   str | None = None
    teacher_name: str | None = None
