## Контекст проекта

Электронный школьный журнал на FastAPI + PostgreSQL.
Одна школа, без мультитенантности.

## Стек

- **Python** 3.12+
- **FastAPI** — API-слой
- **SQLAlchemy** 2.0 (async) — ORM
- **Alembic** — миграции
- **Pydantic** v2 — валидация
- **asyncpg** — драйвер PostgreSQL
- **passlib[bcrypt]** — хэширование паролей
- **PyJWT** — JWT токены (бессрочные, без refresh)
- **PostgreSQL** 15+

## Структура проекта


app/
├── main.py                  # FastAPI app, подключение роутеров
├── core/
│   ├── config.py            # Settings через pydantic-settings
│   ├── database.py          # async engine, get_db, Base
│   └── security.py          # JWT encode/decode, bcrypt
├── models/                  # SQLAlchemy ORM модели
│   ├── user.py
│   ├── subject.py
│   ├── class_.py
│   ├── lesson.py
│   ├── grade.py
│   ├── attendance.py
│   └── notification.py
├── schemas/                 # Pydantic схемы (Request/Response)
│   ├── user.py
│   ├── subject.py
│   ├── class_.py
│   ├── lesson.py
│   ├── grade.py
│   ├── attendance.py
│   └── notification.py
├── routers/                 # Эндпоинты, сгруппированные по сущностям
│   ├── auth.py
│   ├── users.py
│   ├── subjects.py
│   ├── classes.py
│   ├── lessons.py
│   ├── grades.py
│   ├── attendances.py
│   └── notifications.py
├── dependencies.py          # get_current_user, require_role
└── migrations/              # Alembic
    ├── env.py
    └── versions/


## База данных — таблицы

### Схема (уже создана вручную в pgAdmin)

users
├── teacher_profiles       (1:1, user_id UNIQUE)
├── student_profiles       (1:1, user_id UNIQUE)
├── class_students         (M:M класс ↔ ученик)
├── teacher_classes        (M:M учитель ↔ класс)
├── parent_student         (M:M родитель ↔ ученик)
├── grades                 (оценки)
├── attendances            (посещаемость)
├── notifications          (уведомления)
└── lessons                (уроки)
     ├── grades
     └── attendances

subjects
classes
lessons

### ENUM типы в PostgreSQL

user_role: admin | vice_principal | teacher | student | parent
attendance_status: present | absent | late | excused

### Ключевые ограничения БД

- `users.first_name / last_name` — только русские буквы, начинается с заглавной: `^[А-ЯЁ][а-яё\-]+$`
- `users.email` — валидный email формат
- `users.password_hash` — длина >= 60 (bcrypt)
- `classes.name` — формат `^[1-9][0-9]?[А-ЯЁ]$` (например `10А`)
- `classes.academic_year` — BETWEEN 2000 AND 2100
- `grades.value` — BETWEEN 1 AND 5
- `lessons.date` — от 2000-01-01 до CURRENT_DATE + 1 год
- `UNIQUE(lesson_id, student_id)` — в grades и attendances
- `UNIQUE(student_id, academic_year)` — в class_students
- `UNIQUE(teacher_id, class_id)` — в teacher_classes
- `parent_student.parent_id <> student_id` — нельзя быть своим родителем

## Роли и доступ

| Роль            | Возможности                                                  |
|-----------------|--------------------------------------------------------------|
| `admin`         | Полный доступ ко всем эндпоинтам                             |
| `vice_principal`| Просмотр всех данных, управление классами и расписанием      |
| `teacher`       | CRUD оценок и посещаемости только в своих классах            |
| `student`       | Просмотр своих оценок, посещаемости, уведомлений             |
| `parent`        | Просмотр данных своих детей, своих уведомлений               |

## Аутентификация

- JWT без срока действия (без exp, без refresh токенов)
- Алгоритм: HS256
- Payload: `{ "sub": "<user_uuid>", "role": "<role>" }`
- Header: `Authorization: Bearer <token>`
- Эндпоинт: `POST /auth/login` → возвращает `access_token`

## Правила написания кода

### Общие

- Весь код асинхронный (`async/await`)
- Никаких синхронных операций в роутерах и сервисах
- Все строки, даты, UUID — типизированы через Pydantic и аннотации Python
- Нет прямых SQL-запросов — только SQLAlchemy ORM
- Исключение: сложные аналитические запросы — через `text()` с явными параметрами

### Models (SQLAlchemy)

- Использовать `Mapped[T]` и `mapped_column()` — новый стиль SQLAlchemy 2.0
- Все FK объявлять явно с `ForeignKey(..., ondelete="...")`
- Relationships объявлять через `relationship()` с `lazy="selectin"` для вложенных объектов
- ENUM поля — через `SAEnum(..., name="...", create_type=False)`, тип уже создан в БД

# Пример правильной модели
class User(Base):
    __tablename__ = "users"

    id:         Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email:      Mapped[str]       = mapped_column(String(255), unique=True)
    role:       Mapped[str]       = mapped_column(SAEnum("admin", ..., name="user_role", create_type=False))
    is_active:  Mapped[bool]      = mapped_column(default=True)
    created_at: Mapped[datetime]  = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime]  = mapped_column(DateTime(timezone=True), server_default=func.now())

### Schemas (Pydantic v2)

- Разделять схемы на `Create`, `Update`, `Response` для каждой сущности
- `Response`-схемы всегда содержат `id`, `created_at`
- `Update`-схемы — все поля Optional
- Использовать `model_config = ConfigDict(from_attributes=True)`
- UUID передавать как `uuid.UUID`, не как строку
- Даты — `datetime` с timezone (`datetime` + `AwareDatetime`)

# Пример разделения схем
class GradeCreate(BaseModel):
    lesson_id:  uuid.UUID
    student_id: uuid.UUID
    value:      int = Field(..., ge=1, le=5)
    comment:    str | None = Field(None, min_length=2, max_length=1000)

class GradeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:         uuid.UUID
    lesson_id:  uuid.UUID
    student_id: uuid.UUID
    value:      int
    comment:    str | None
    created_at: datetime

### Routers (FastAPI)

- Каждый роутер — отдельный файл в `routers/`
- Prefix и tags обязательны
- Каждый эндпоинт имеет `summary` и явные `status_code`
- Использовать `Depends(get_db)` и `Depends(get_current_user)` везде
- Проверку прав делать через `Depends(require_role(...))`
- Не писать бизнес-логику прямо в роутере — выносить в отдельные функции если логика сложная

# Пример структуры роутера
router = APIRouter(prefix="/grades", tags=["Grades"])

@router.post("/", response_model=GradeResponse, status_code=201,
             summary="Выставить оценку ученику")
async def create_grade(
    body: GradeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("teacher", "admin")),
):
    ...

### HTTP статус коды

| Ситуация                        | Код |
|---------------------------------|-----|
| Успешное создание               | 201 |
| Успешное чтение / обновление    | 200 |
| Успешное удаление               | 204 |
| Не найдено                      | 404 |
| Нет прав                        | 403 |
| Не авторизован                  | 401 |
| Ошибка валидации                | 422 |
| Конфликт (дубликат)             | 409 |

### Обработка ошибок

- Всегда использовать `HTTPException` с понятным `detail` на русском языке
- Дублирование уникальных полей → 409
- Объект не найден → 404
- Доступ запрещён → 403

# Пример
result = await db.get(Grade, grade_id)
if not result:
    raise HTTPException(status_code=404, detail="Оценка не найдена")
```

## Зависимости (dependencies.py)

# get_current_user — всегда возвращает User или кидает 401
# require_role(*roles) — фабрика, возвращает Depends с проверкой роли

current_user = Depends(get_current_user)
admin_only   = Depends(require_role("admin"))
teacher_up   = Depends(require_role("teacher", "admin", "vice_principal"))

## Переменные окружения (.env)

DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/school_journal
SECRET_KEY=your-secret-key-min-32-chars

## Запрещено

- Синхронные `db.execute()` без `await`
- Хранение паролей в открытом виде
- Передача `password_hash` в Response-схемах
- Прямые `INSERT/UPDATE` через `text()` там где можно через ORM
- Логика авторизации внутри моделей
- Хардкод UUID, паролей, ключей в коде
- `SELECT *` — всегда явные колонки или ORM-объекты

## Порядок разработки (текущий статус)

- [x] Схема БД спроектирована и создана в pgAdmin
- [ ] Настройка проекта (pyproject.toml / requirements.txt)
- [ ] core/ — config, database, security
- [ ] models/ — все ORM модели
- [ ] schemas/ — все Pydantic схемы
- [ ] dependencies.py — get_current_user, require_role
- [ ] routers/auth.py — POST /auth/login
- [ ] routers/users.py — CRUD пользователей
- [ ] routers/subjects.py — справочник предметов
- [ ] routers/classes.py — управление классами
- [ ] routers/lessons.py — уроки
- [ ] routers/grades.py — оценки
- [ ] routers/attendances.py — посещаемость
- [ ] routers/notifications.py — уведомления
