import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

AttendanceStatus = Literal["present", "absent", "late", "excused"]


class AttendanceCreate(BaseModel):
    lesson_id:  uuid.UUID
    student_id: uuid.UUID
    status:     AttendanceStatus = "present"


class AttendanceUpdate(BaseModel):
    status: AttendanceStatus | None = None


class AttendanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:         uuid.UUID
    lesson_id:  uuid.UUID
    student_id: uuid.UUID
    status:     str
    created_at: datetime
    updated_at: datetime
