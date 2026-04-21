import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import hash_password
from app.dependencies import get_current_user, require_role
from app.models.user import User, TeacherProfile, StudentProfile, parent_student
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse,
    TeacherProfileCreate, TeacherProfileUpdate, TeacherProfileResponse,
    StudentProfileCreate, StudentProfileUpdate, StudentProfileResponse,
)
from app.schemas.class_ import ParentStudentCreate, ParentStudentResponse

router = APIRouter(prefix="/users", tags=["Users"])

_ADMIN = require_role("admin")
_ADMIN_VP = require_role("admin", "vice_principal")


def _user_opts():
    return [
        selectinload(User.teacher_profile),
        selectinload(User.student_profile),
        selectinload(User.children),
    ]


async def _get_user_full(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id).options(*_user_opts()))
    return result.scalar_one_or_none()


# ── Пользователи ─────────────────────────────────────────────────────────────

@router.get("/", response_model=list[UserResponse], status_code=200, summary="Список пользователей")
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(_ADMIN_VP),
):
    result = await db.execute(select(User).options(*_user_opts()))
    return result.scalars().all()


@router.get("/me", response_model=UserResponse, status_code=200, summary="Текущий пользователь")
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/{user_id}", response_model=UserResponse, status_code=200, summary="Получить пользователя по ID")
async def get_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("admin", "vice_principal") and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")

    user = await _get_user_full(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return user


@router.post("/", response_model=UserResponse, status_code=201, summary="Создать пользователя")
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_ADMIN_VP),
):
    if current_user.role == "vice_principal" and body.role == "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Завуч не может создавать администраторов")

    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email уже занят")

    user = User(
        email=str(body.email),
        password_hash=hash_password(body.password),
        role=body.role,
        first_name=body.first_name,
        last_name=body.last_name,
        middle_name=body.middle_name,
    )
    db.add(user)
    await db.commit()
    user = await _get_user_full(db, user.id)
    return user


@router.patch("/{user_id}", response_model=UserResponse, status_code=200, summary="Обновить пользователя")
async def update_user(
    user_id: uuid.UUID,
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    is_vp = current_user.role == "vice_principal"
    is_admin = current_user.role == "admin"

    if not is_admin and not is_vp and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")

    if is_vp and current_user.id != user_id:
        data = body.model_dump(exclude_unset=True)
        if "is_active" in data:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Завуч не может деактивировать аккаунты")

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    data = body.model_dump(exclude_unset=True)

    if is_vp and current_user.id != user_id:
        data.pop("is_active", None)
        data.pop("role", None)

    if "password" in data:
        user.password_hash = hash_password(data.pop("password"))
    if "email" in data:
        data["email"] = str(data["email"])

    for field, value in data.items():
        setattr(user, field, value)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email уже занят")

    user = await _get_user_full(db, user_id)
    return user


@router.delete("/{user_id}", status_code=204, summary="Удалить пользователя")
async def delete_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(_ADMIN_VP),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    await db.delete(user)
    await db.commit()


# ── Профиль учителя ───────────────────────────────────────────────────────────

@router.post("/{user_id}/teacher-profile", response_model=TeacherProfileResponse, status_code=201,
             summary="Создать профиль учителя")
async def create_teacher_profile(
    user_id: uuid.UUID,
    body: TeacherProfileCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(_ADMIN_VP),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    if user.role != "teacher":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Пользователь не является учителем")

    result = await db.execute(select(TeacherProfile).where(TeacherProfile.user_id == user_id))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Профиль учителя уже существует")

    profile = TeacherProfile(user_id=user_id, subject_id=body.subject_id)
    db.add(profile)
    try:
        await db.commit()
        await db.refresh(profile)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Предмет не найден")
    return profile


@router.patch("/{user_id}/teacher-profile", response_model=TeacherProfileResponse, status_code=200,
              summary="Обновить профиль учителя")
async def update_teacher_profile(
    user_id: uuid.UUID,
    body: TeacherProfileUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(_ADMIN_VP),
):
    result = await db.execute(select(TeacherProfile).where(TeacherProfile.user_id == user_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Профиль учителя не найден")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    try:
        await db.commit()
        await db.refresh(profile)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Предмет не найден")
    return profile


# ── Профиль ученика ───────────────────────────────────────────────────────────

@router.post("/{user_id}/student-profile", response_model=StudentProfileResponse, status_code=201,
             summary="Создать профиль ученика")
async def create_student_profile(
    user_id: uuid.UUID,
    body: StudentProfileCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(_ADMIN_VP),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    if user.role != "student":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Пользователь не является учеником")

    result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == user_id))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Профиль ученика уже существует")

    profile = StudentProfile(
        user_id=user_id,
        date_of_birth=body.date_of_birth,
        record_number=body.record_number,
    )
    db.add(profile)
    try:
        await db.commit()
        await db.refresh(profile)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Номер личного дела уже занят")
    return profile


@router.patch("/{user_id}/student-profile", response_model=StudentProfileResponse, status_code=200,
              summary="Обновить профиль ученика")
async def update_student_profile(
    user_id: uuid.UUID,
    body: StudentProfileUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(_ADMIN_VP),
):
    result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == user_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Профиль ученика не найден")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    try:
        await db.commit()
        await db.refresh(profile)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Номер личного дела уже занят")
    return profile


# ── Связь родитель–ребёнок ────────────────────────────────────────────────────

@router.post("/parents/{parent_id}/children/{student_id}", response_model=ParentStudentResponse,
             status_code=201, summary="Привязать ребёнка к родителю")
async def add_child(
    parent_id: uuid.UUID,
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(_ADMIN_VP),
):
    parent = await db.get(User, parent_id)
    student = await db.get(User, student_id)

    if not parent or parent.role != "parent":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Родитель не найден")
    if not student or student.role != "student":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ученик не найден")
    if parent_id == student_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Нельзя быть своим родителем")

    exists = await db.execute(
        select(parent_student).where(
            parent_student.c.parent_id == parent_id,
            parent_student.c.student_id == student_id,
        )
    )
    if exists.first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Связь уже существует")

    await db.execute(parent_student.insert().values(parent_id=parent_id, student_id=student_id))
    await db.commit()
    return ParentStudentResponse(parent_id=parent_id, student_id=student_id)


@router.delete("/parents/{parent_id}/children/{student_id}", status_code=204,
               summary="Удалить связь родитель–ребёнок")
async def remove_child(
    parent_id: uuid.UUID,
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(_ADMIN_VP),
):
    result = await db.execute(
        select(parent_student).where(
            parent_student.c.parent_id == parent_id,
            parent_student.c.student_id == student_id,
        )
    )
    if not result.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Связь не найдена")

    await db.execute(
        parent_student.delete().where(
            parent_student.c.parent_id == parent_id,
            parent_student.c.student_id == student_id,
        )
    )
    await db.commit()
