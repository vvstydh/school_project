import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NotificationCreate(BaseModel):
    recipient_id: uuid.UUID
    title:        str = Field(..., min_length=2, max_length=255)
    body:         str = Field(..., min_length=2, max_length=5000)


class SenderShort(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:         uuid.UUID
    first_name: str
    last_name:  str


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:           uuid.UUID
    recipient_id: uuid.UUID
    sender_id:    uuid.UUID | None
    sender:       SenderShort | None = None
    title:        str
    body:         str
    is_read:      bool
    created_at:   datetime
