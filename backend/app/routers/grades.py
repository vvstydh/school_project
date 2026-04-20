import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.class_ import ClassStudent, TeacherClass
from app.models.grade import Grade
from app.models.lesson import Lesson
from app.models.user import User
from app.schemas.grade import GradeCreate, GradeUpdate, GradeResponse

router = APIRouter(prefix="/grades", tags=["Grades"])

_ADMIN_VP = require_role("admin", "vice_principal")
_TEACHER_ADMIN = require_role("teacher", "admin", "vice_principal")


async def _assert_teacher_controls_lesson(teacher_id: uuid.UUID, lesson: Lesson, db: AsyncSession):
    result = await db.execute(
        select(TeacherClass).where(
            TeacherClass.teacher_id == teacher_id,
            TeacherClass.class_id == lesson.class_id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Учитель не ведёт этот класс")


@router.get("/", response_model=list[GradeResponse], status_code=200, summary="Список оценок")
async def list_grades(
    lesson_id: uuid.UUID | None = None,
    student_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Grade)

    if current_user.role == "student":
        query = query.where(Grade.student_id == current_user.id)
    elif current_user.role == "parent":
        children_ids = [c.id for c in current_user.children]
        query = query.where(Grade.student_id.in_(children_ids))
    elif current_user.role == "teacher":
        teacher_class_ids = select(TeacherClass.class_id).where(TeacherClass.teacher_id == current_user.id)
        lesson_ids = select(Lesson.id).where(Lesson.class_id.in_(teacher_class_ids))
        query = query.where(Grade.lesson_id.in_(lesson_ids))

    if lesson_id:
        query = query.where(Grade.lesson_id == lesson_id)
    if student_id:
        if current_user.role == "student" and student_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
        query = query.where(Grade.student_id == student_id)

    result = await db.execute(query.order_by(Grade.created_at.desc()))
    return result.scalars().all()


@router.get("/{grade_id}", response_model=GradeResponse, status_code=200, summary="Получить оценку по ID")
async def get_grade(
    grade_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    grade = await db.get(Grade, grade_id)
    if not grade:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Оценка не найдена")

    if current_user.role == "student" and grade.student_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
    if current_user.role == "parent":
        children_ids = [c.id for c in current_user.children]
        if grade.student_id not in children_ids:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")

    return grade


@router.post("/", response_model=GradeResponse, status_code=201, summary="Выставить оценку")
async def create_grade(
    body: GradeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_TEACHER_ADMIN),
):
    lesson = await db.get(Lesson, body.lesson_id)
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Урок не найден")

    if current_user.role == "teacher":
        await _assert_teacher_controls_lesson(current_user.id, lesson, db)

    student = await db.get(User, body.student_id)
    if not student or student.role != "student":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ученик не найден")

    # Проверяем что ученик числится в классе урока
    result = await db.execute(
        select(ClassStudent).where(
            ClassStudent.class_id == lesson.class_id,
            ClassStudent.student_id == body.student_id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Ученик не числится в классе этого урока")

    grade = Grade(
        lesson_id=body.lesson_id,
        student_id=body.student_id,
        value=body.value,
        comment=body.comment,
    )
    db.add(grade)
    try:
        await db.commit()
        await db.refresh(grade)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Оценка этому ученику за данный урок уже выставлена")
    return grade


@router.patch("/{grade_id}", response_model=GradeResponse, status_code=200, summary="Изменить оценку")
async def update_grade(
    grade_id: uuid.UUID,
    body: GradeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_TEACHER_ADMIN),
):
    grade = await db.get(Grade, grade_id)
    if not grade:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Оценка не найдена")

    if current_user.role == "teacher":
        lesson = await db.get(Lesson, grade.lesson_id)
        await _assert_teacher_controls_lesson(current_user.id, lesson, db)

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(grade, field, value)

    await db.commit()
    await db.refresh(grade)
    return grade


@router.delete("/{grade_id}", status_code=204, summary="Удалить оценку")
async def delete_grade(
    grade_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_TEACHER_ADMIN),
):
    grade = await db.get(Grade, grade_id)
    if not grade:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Оценка не найдена")

    if current_user.role == "teacher":
        lesson = await db.get(Lesson, grade.lesson_id)
        await _assert_teacher_controls_lesson(current_user.id, lesson, db)

    await db.delete(grade)
    await db.commit()
