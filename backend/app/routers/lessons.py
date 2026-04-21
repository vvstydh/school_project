import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.class_ import TeacherClass
from app.models.lesson import Lesson
from app.models.user import User
from app.schemas.lesson import LessonCreate, LessonUpdate, LessonResponse

router = APIRouter(prefix="/lessons", tags=["Lessons"])

_ADMIN_VP = require_role("admin", "vice_principal")
_ADMIN_VP_TEACHER = require_role("admin", "vice_principal", "teacher")


async def _assert_teacher_owns_class(teacher_id: uuid.UUID, class_id: uuid.UUID, db: AsyncSession):
    result = await db.execute(
        select(TeacherClass).where(
            TeacherClass.teacher_id == teacher_id,
            TeacherClass.class_id == class_id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Учитель не прикреплён к этому классу")


@router.get("/", response_model=list[LessonResponse], status_code=200, summary="Список уроков")
async def list_lessons(
    class_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_ADMIN_VP_TEACHER),
):
    query = select(Lesson)
    if class_id:
        query = query.where(Lesson.class_id == class_id)
    if current_user.role == "teacher":
        query = query.where(Lesson.teacher_id == current_user.id)
    result = await db.execute(query.order_by(Lesson.date.desc()))
    return result.scalars().all()


@router.get("/{lesson_id}", response_model=LessonResponse, status_code=200, summary="Получить урок по ID")
async def get_lesson(
    lesson_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lesson = await db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Урок не найден")

    if current_user.role == "teacher" and lesson.teacher_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")

    return lesson


@router.post("/", response_model=LessonResponse, status_code=201, summary="Создать урок")
async def create_lesson(
    body: LessonCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_ADMIN_VP),
):
    if current_user.role == "teacher":
        if body.teacher_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Учитель может создавать уроки только от своего имени")
        await _assert_teacher_owns_class(current_user.id, body.class_id, db)

    lesson = Lesson(
        class_id=body.class_id,
        teacher_id=body.teacher_id,
        subject_id=body.subject_id,
        date=body.date,
        topic=body.topic,
    )
    db.add(lesson)
    try:
        await db.commit()
        await db.refresh(lesson)
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ошибка создания урока")
    return lesson


@router.patch("/{lesson_id}", response_model=LessonResponse, status_code=200, summary="Обновить урок")
async def update_lesson(
    lesson_id: uuid.UUID,
    body: LessonUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_ADMIN_VP_TEACHER),
):
    lesson = await db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Урок не найден")

    if current_user.role == "teacher" and lesson.teacher_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")

    data = body.model_dump(exclude_unset=True)
    if current_user.role == "teacher":
        data.pop("date", None)  # teachers can only update topic

    for field, value in data.items():
        setattr(lesson, field, value)

    await db.commit()
    await db.refresh(lesson)
    return lesson


@router.delete("/{lesson_id}", status_code=204, summary="Удалить урок")
async def delete_lesson(
    lesson_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(_ADMIN_VP),
):
    lesson = await db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Урок не найден")

    await db.delete(lesson)
    await db.commit()
