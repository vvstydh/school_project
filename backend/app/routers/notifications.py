import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationCreate, NotificationResponse

router = APIRouter(prefix="/notifications", tags=["Notifications"])

_ADMIN_VP_TEACHER = require_role("admin", "vice_principal", "teacher")
_ADMIN = require_role("admin")


@router.get("/", response_model=list[NotificationResponse], status_code=200,
            summary="Список уведомлений текущего пользователя")
async def list_notifications(
    unread_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Notification).where(Notification.recipient_id == current_user.id)
    if unread_only:
        query = query.where(Notification.is_read == False)  # noqa: E712
    result = await db.execute(query.order_by(Notification.created_at.desc()))
    return result.scalars().all()


@router.get("/{notification_id}", response_model=NotificationResponse, status_code=200,
            summary="Получить уведомление по ID")
async def get_notification(
    notification_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = await db.get(Notification, notification_id)
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Уведомление не найдено")
    if notification.recipient_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
    return notification


@router.post("/", response_model=NotificationResponse, status_code=201, summary="Создать уведомление")
async def create_notification(
    body: NotificationCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(_ADMIN_VP_TEACHER),
):
    recipient = await db.get(User, body.recipient_id)
    if not recipient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Получатель не найден")

    notification = Notification(
        recipient_id=body.recipient_id,
        title=body.title,
        body=body.body,
    )
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return notification


@router.patch("/{notification_id}/read", response_model=NotificationResponse, status_code=200,
              summary="Отметить уведомление как прочитанное")
async def mark_as_read(
    notification_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = await db.get(Notification, notification_id)
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Уведомление не найдено")
    if notification.recipient_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")

    notification.is_read = True
    await db.commit()
    await db.refresh(notification)
    return notification


@router.delete("/{notification_id}", status_code=204, summary="Удалить уведомление")
async def delete_notification(
    notification_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = await db.get(Notification, notification_id)
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Уведомление не найдено")
    if notification.recipient_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")

    await db.delete(notification)
    await db.commit()
