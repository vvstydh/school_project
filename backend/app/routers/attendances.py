import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.attendance import Attendance
from app.models.class_ import ClassStudent, TeacherClass
from app.models.lesson import Lesson
from app.models.user import User
from app.schemas.attendance import AttendanceCreate, AttendanceUpdate, AttendanceResponse

router = APIRouter(prefix="/attendances", tags=["Attendances"])

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


@router.get("/", response_model=list[AttendanceResponse], status_code=200, summary="Список записей посещаемости")
async def list_attendances(
    lesson_id: uuid.UUID | None = None,
    student_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Attendance)

    if current_user.role == "student":
        query = query.where(Attendance.student_id == current_user.id)
    elif current_user.role == "parent":
        children_ids = [c.id for c in current_user.children]
        query = query.where(Attendance.student_id.in_(children_ids))
    elif current_user.role == "teacher":
        teacher_class_ids = select(TeacherClass.class_id).where(TeacherClass.teacher_id == current_user.id)
        lesson_ids = select(Lesson.id).where(Lesson.class_id.in_(teacher_class_ids))
        query = query.where(Attendance.lesson_id.in_(lesson_ids))

    if lesson_id:
        query = query.where(Attendance.lesson_id == lesson_id)
    if student_id:
        if current_user.role == "student" and student_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
        query = query.where(Attendance.student_id == student_id)

    result = await db.execute(query.order_by(Attendance.created_at.desc()))
    return result.scalars().all()


@router.get("/{attendance_id}", response_model=AttendanceResponse, status_code=200,
            summary="Получить запись посещаемости по ID")
async def get_attendance(
    attendance_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = await db.get(Attendance, attendance_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Запись посещаемости не найдена")

    if current_user.role == "student" and record.student_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
    if current_user.role == "parent":
        children_ids = [c.id for c in current_user.children]
        if record.student_id not in children_ids:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")

    return record


@router.post("/", response_model=AttendanceResponse, status_code=201, summary="Отметить посещаемость")
async def create_attendance(
    body: AttendanceCreate,
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

    result = await db.execute(
        select(ClassStudent).where(
            ClassStudent.class_id == lesson.class_id,
            ClassStudent.student_id == body.student_id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Ученик не числится в классе этого урока")

    record = Attendance(
        lesson_id=body.lesson_id,
        student_id=body.student_id,
        status=body.status,
    )
    db.add(record)
    try:
        await db.commit()
        await db.refresh(record)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Посещаемость этому ученику за данный урок уже отмечена")
    return record


@router.patch("/{attendance_id}", response_model=AttendanceResponse, status_code=200,
              summary="Изменить статус посещаемости")
async def update_attendance(
    attendance_id: uuid.UUID,
    body: AttendanceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_TEACHER_ADMIN),
):
    record = await db.get(Attendance, attendance_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Запись посещаемости не найдена")

    if current_user.role == "teacher":
        lesson = await db.get(Lesson, record.lesson_id)
        await _assert_teacher_controls_lesson(current_user.id, lesson, db)

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(record, field, value)

    await db.commit()
    await db.refresh(record)
    return record


@router.delete("/{attendance_id}", status_code=204, summary="Удалить запись посещаемости")
async def delete_attendance(
    attendance_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_TEACHER_ADMIN),
):
    record = await db.get(Attendance, attendance_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Запись посещаемости не найдена")

    if current_user.role == "teacher":
        lesson = await db.get(Lesson, record.lesson_id)
        await _assert_teacher_controls_lesson(current_user.id, lesson, db)

    await db.delete(record)
    await db.commit()
