import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.subject import Subject
from app.models.user import User
from app.schemas.subject import SubjectCreate, SubjectUpdate, SubjectResponse

router = APIRouter(prefix="/subjects", tags=["Subjects"])

_ADMIN = require_role("admin")


@router.get("/", response_model=list[SubjectResponse], status_code=200, summary="Список предметов")
async def list_subjects(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Subject).order_by(Subject.name))
    return result.scalars().all()


@router.get("/{subject_id}", response_model=SubjectResponse, status_code=200, summary="Получить предмет по ID")
async def get_subject(
    subject_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    subject = await db.get(Subject, subject_id)
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Предмет не найден")
    return subject


@router.post("/", response_model=SubjectResponse, status_code=201, summary="Создать предмет")
async def create_subject(
    body: SubjectCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(_ADMIN),
):
    subject = Subject(name=body.name)
    db.add(subject)
    try:
        await db.commit()
        await db.refresh(subject)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Предмет с таким названием уже существует")
    return subject


@router.patch("/{subject_id}", response_model=SubjectResponse, status_code=200, summary="Обновить предмет")
async def update_subject(
    subject_id: uuid.UUID,
    body: SubjectUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(_ADMIN),
):
    subject = await db.get(Subject, subject_id)
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Предмет не найден")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(subject, field, value)

    try:
        await db.commit()
        await db.refresh(subject)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Предмет с таким названием уже существует")
    return subject


@router.delete("/{subject_id}", status_code=204, summary="Удалить предмет")
async def delete_subject(
    subject_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(_ADMIN),
):
    subject = await db.get(Subject, subject_id)
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Предмет не найден")
    try:
        await db.delete(subject)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Предмет используется и не может быть удалён")
