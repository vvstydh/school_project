import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.class_ import Class, ClassStudent, TeacherClass
from app.models.user import User
from app.schemas.class_ import (
    ClassCreate, ClassUpdate, ClassResponse,
    ClassStudentCreate, ClassStudentResponse,
    TeacherClassCreate, TeacherClassResponse,
)

router = APIRouter(prefix="/classes", tags=["Classes"])

_ADMIN = require_role("admin")
_ADMIN_VP = require_role("admin", "vice_principal")
_ADMIN_VP_TEACHER = require_role("admin", "vice_principal", "teacher")


@router.get("/", response_model=list[ClassResponse], status_code=200, summary="Список классов")
async def list_classes(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(_ADMIN_VP_TEACHER),
):
    result = await db.execute(select(Class).order_by(Class.academic_year, Class.name))
    return result.scalars().all()


@router.get("/{class_id}", response_model=ClassResponse, status_code=200, summary="Получить класс по ID")
async def get_class(
    class_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(_ADMIN_VP_TEACHER),
):
    cls = await db.get(Class, class_id)
    if not cls:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Класс не найден")
    return cls


@router.post("/", response_model=ClassResponse, status_code=201, summary="Создать класс")
async def create_class(
    body: ClassCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(_ADMIN_VP),
):
    cls = Class(
        name=body.name,
        academic_year=body.academic_year,
        vice_principal_id=body.vice_principal_id,
    )
    db.add(cls)
    try:
        await db.commit()
        await db.refresh(cls)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Класс с таким названием и учебным годом уже существует")
    return cls


@router.patch("/{class_id}", response_model=ClassResponse, status_code=200, summary="Обновить класс")
async def update_class(
    class_id: uuid.UUID,
    body: ClassUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(_ADMIN_VP),
):
    cls = await db.get(Class, class_id)
    if not cls:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Класс не найден")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(cls, field, value)

    try:
        await db.commit()
        await db.refresh(cls)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Класс с таким названием и учебным годом уже существует")
    return cls


@router.delete("/{class_id}", status_code=204, summary="Удалить класс")
async def delete_class(
    class_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(_ADMIN),
):
    cls = await db.get(Class, class_id)
    if not cls:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Класс не найден")
    await db.delete(cls)
    await db.commit()


# ── Ученики в классе ──────────────────────────────────────────────────────────

@router.get("/{class_id}/students", response_model=list[ClassStudentResponse], status_code=200,
            summary="Список учеников класса")
async def list_class_students(
    class_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(_ADMIN_VP_TEACHER),
):
    cls = await db.get(Class, class_id)
    if not cls:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Класс не найден")

    result = await db.execute(select(ClassStudent).where(ClassStudent.class_id == class_id))
    return result.scalars().all()


@router.post("/{class_id}/students", response_model=ClassStudentResponse, status_code=201,
             summary="Добавить ученика в класс")
async def add_student_to_class(
    class_id: uuid.UUID,
    body: ClassStudentCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(_ADMIN_VP),
):
    cls = await db.get(Class, class_id)
    if not cls:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Класс не найден")

    student = await db.get(User, body.student_id)
    if not student or student.role != "student":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ученик не найден")

    link = ClassStudent(
        class_id=class_id,
        student_id=body.student_id,
        academic_year=body.academic_year,
        **({"enrolled_at": body.enrolled_at} if body.enrolled_at else {}),
    )
    db.add(link)
    try:
        await db.commit()
        await db.refresh(link)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Ученик уже числится в классе в этом учебном году")
    return link


@router.delete("/{class_id}/students/{student_id}", status_code=204,
               summary="Удалить ученика из класса")
async def remove_student_from_class(
    class_id: uuid.UUID,
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(_ADMIN_VP),
):
    result = await db.execute(
        select(ClassStudent).where(
            ClassStudent.class_id == class_id,
            ClassStudent.student_id == student_id,
        )
    )
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ученик не числится в этом классе")
    await db.delete(link)
    await db.commit()


# ── Учителя в классе ──────────────────────────────────────────────────────────

@router.get("/{class_id}/teachers", response_model=list[TeacherClassResponse], status_code=200,
            summary="Список учителей класса")
async def list_class_teachers(
    class_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(_ADMIN_VP_TEACHER),
):
    cls = await db.get(Class, class_id)
    if not cls:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Класс не найден")

    result = await db.execute(select(TeacherClass).where(TeacherClass.class_id == class_id))
    return result.scalars().all()


@router.post("/{class_id}/teachers", response_model=TeacherClassResponse, status_code=201,
             summary="Прикрепить учителя к классу")
async def add_teacher_to_class(
    class_id: uuid.UUID,
    body: TeacherClassCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(_ADMIN_VP),
):
    cls = await db.get(Class, class_id)
    if not cls:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Класс не найден")

    teacher = await db.get(User, body.teacher_id)
    if not teacher or teacher.role != "teacher":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Учитель не найден")

    link = TeacherClass(teacher_id=body.teacher_id, class_id=class_id)
    db.add(link)
    try:
        await db.commit()
        await db.refresh(link)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Учитель уже прикреплён к этому классу")
    return link


@router.delete("/{class_id}/teachers/{teacher_id}", status_code=204,
               summary="Открепить учителя от класса")
async def remove_teacher_from_class(
    class_id: uuid.UUID,
    teacher_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(_ADMIN_VP),
):
    result = await db.execute(
        select(TeacherClass).where(
            TeacherClass.class_id == class_id,
            TeacherClass.teacher_id == teacher_id,
        )
    )
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Учитель не прикреплён к этому классу")
    await db.delete(link)
    await db.commit()
