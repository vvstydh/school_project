# Документация бэкенда — Зурнал

## Содержание

1. [Обзор архитектуры](#1-обзор-архитектуры)
2. [Технологический стек](#2-технологический-стек)
3. [Структура директорий](#3-структура-директорий)
4. [Запуск и конфигурация](#4-запуск-и-конфигурация)
5. [Точка входа — main.py](#5-точка-входа--mainpy)
6. [Ядро приложения — core/](#6-ядро-приложения--core)
7. [Модели ORM — models/](#7-модели-orm--models)
8. [Pydantic-схемы — schemas/](#8-pydantic-схемы--schemas)
9. [Зависимости — dependencies.py](#9-зависимости--dependenciespy)
10. [Middleware — middleware.py](#10-middleware--middlewarepy)
11. [Роутеры — routers/](#11-роутеры--routers)
12. [Схема авторизации](#12-схема-авторизации)
13. [Жизненный цикл HTTP-запроса](#13-жизненный-цикл-http-запроса)
14. [Каскады удаления ORM](#14-каскады-удаления-orm)
15. [Утилиты](#15-утилиты)

---

## 1. Обзор архитектуры

Бэкенд — REST API на **FastAPI** с асинхронной работой с БД через **SQLAlchemy 2.0 async** и драйвером **asyncpg**. Все операции с БД неблокирующие.

```
┌─────────────────────────────────────────────────────────┐
│                    HTTP-запрос                          │
│                        │                               │
│              LoggingMiddleware                          │
│                        │                               │
│              CORSMiddleware                             │
│                        │                               │
│              FastAPI Router                             │
│                        │                               │
│          dependencies.py (get_current_user)             │
│                        │                               │
│              Router handler                             │
│                  /    |    \                            │
│           Schema    ORM    DB (asyncpg → PostgreSQL)    │
└─────────────────────────────────────────────────────────┘
```

**Принципы:**
- Один `AsyncSession` на HTTP-запрос (через `Depends(get_db)`)
- Все роутеры требуют JWT-токен, кроме `/auth/login` и `/health`
- Валидация входных данных — Pydantic v2 (схемы)
- Ответы сериализуются через `response_model` Pydantic-схемы

---

## 2. Технологический стек

| Библиотека | Версия | Назначение |
|------------|--------|-----------|
| `fastapi` | 0.115.5 | Веб-фреймворк, роутинг, DI |
| `uvicorn[standard]` | 0.32.1 | ASGI-сервер |
| `sqlalchemy` | 2.0.36 | ORM, async-сессии |
| `asyncpg` | 0.30.0 | Асинхронный PostgreSQL-драйвер |
| `pydantic[email]` | 2.10.3 | Валидация данных, схемы |
| `pydantic-settings` | 2.6.1 | Конфигурация через .env |
| `email-validator` | 2.2.0 | Валидация email (для EmailStr) |
| `passlib[bcrypt]` | 1.7.4 | Хеширование паролей |
| `bcrypt` | 4.0.1 | Алгоритм хеширования |
| `PyJWT` | 2.10.1 | JWT-токены |
| `python-multipart` | 0.0.20 | Form-data для `/auth/login` |
| `alembic` | 1.14.0 | Миграции БД (подготовлен, не используется активно) |

---

## 3. Структура директорий

```
backend/
├── Dockerfile                  # Python 3.12-slim, uvicorn --reload
├── requirements.txt            # Зависимости
├── seed_admin.py               # Скрипт создания первого admin-пользователя
└── app/
    ├── __init__.py
    ├── main.py                 # Точка входа FastAPI-приложения
    ├── dependencies.py         # get_current_user, require_role
    ├── middleware.py           # LoggingMiddleware (логирует все запросы)
    ├── core/
    │   ├── __init__.py
    │   ├── config.py           # Settings (DATABASE_URL, SECRET_KEY из .env)
    │   ├── database.py         # Движок SQLAlchemy, Base, get_db
    │   ├── logger.py           # Настройка логгера (файл + консоль)
    │   └── security.py         # hash_password, verify_password, JWT
    ├── migrations/
    │   └── env.py              # Alembic env (async-конфигурация)
    ├── models/
    │   ├── __init__.py         # Реэкспорт всех моделей для регистрации в Base
    │   ├── user.py             # User, TeacherProfile, StudentProfile, parent_student
    │   ├── subject.py          # Subject
    │   ├── class_.py           # Class, ClassStudent, TeacherClass
    │   ├── lesson.py           # Lesson
    │   ├── grade.py            # Grade
    │   ├── attendance.py       # Attendance
    │   └── notification.py     # Notification
    ├── schemas/
    │   ├── __init__.py
    │   ├── user.py             # UserCreate/Update/Response, профили, связи родитель-ребёнок
    │   ├── subject.py          # SubjectCreate/Update/Response
    │   ├── class_.py           # ClassCreate/Update/Response, ClassStudent*, TeacherClass*, ParentStudent*
    │   ├── lesson.py           # LessonCreate/Update/Response
    │   ├── grade.py            # GradeCreate/Update/Response
    │   ├── attendance.py       # AttendanceCreate/Update/Response
    │   └── notification.py     # NotificationCreate/Response
    └── routers/
        ├── __init__.py         # Реэкспорт всех роутеров
        ├── auth.py             # POST /auth/login
        ├── users.py            # CRUD /users/, профили, родитель↔ребёнок
        ├── subjects.py         # CRUD /subjects/
        ├── classes.py          # CRUD /classes/, ученики и учителя в классе
        ├── lessons.py          # CRUD /lessons/
        ├── grades.py           # CRUD /grades/
        ├── attendances.py      # CRUD /attendances/
        └── notifications.py    # CRUD /notifications/, отметка "прочитано"
```

---

## 4. Запуск и конфигурация

### Docker Compose

```yaml
# docker-compose.yml (фрагмент)
api:
  build: ./backend
  volumes:
    - ./backend/app:/app/app   # hot-reload: изменения в коде → мгновенно в контейнере
  env_file: .env
  ports: ["8000:8000"]
  depends_on:
    db:
      condition: service_healthy
```

**Важно:** volume mount `./backend/app:/app/app` обеспечивает горячую перезагрузку бэкенда — любое изменение `.py`-файла применяется без пересборки образа. Изменения в `requirements.txt` или `Dockerfile` требуют `docker compose up -d --build api`.

### Переменные окружения (`.env`)

| Переменная | Пример | Описание |
|-----------|--------|----------|
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@db:5432/school` | Строка подключения к PostgreSQL (asyncpg-диалект) |
| `SECRET_KEY` | `supersecretkey` | Ключ подписи JWT-токенов |
| `POSTGRES_USER` | `postgres` | Используется в docker-compose healthcheck |
| `POSTGRES_DB` | `school` | Имя базы данных |
| `POSTGRES_PASSWORD` | `...` | Пароль PostgreSQL |
| `POSTGRES_PORT` | `5432` | Порт PostgreSQL на хосте |

### Dockerfile

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

`--reload` включён постоянно — uvicorn следит за изменениями файлов (работает через volume mount в dev-режиме).

---

## 5. Точка входа — `main.py`

**Файл:** `backend/app/main.py`

```python
app = FastAPI(title="Школьный журнал", version="1.0.0")
```

**Что происходит при старте:**

1. Импортируется `app.models` — это регистрирует все ORM-модели в `Base.metadata` (необходимо для Alembic и `create_all`)
2. Подключаются два middleware: `CORSMiddleware` и `LoggingMiddleware`
3. Регистрируются 8 роутеров
4. Устанавливается обработчик `ResponseValidationError` — логирует ошибки сериализации ответов (500)

**CORS-настройка:**
```python
allow_origins=["http://localhost", "http://localhost:80"]
```
Разрешает запросы только с фронтенда на 80-м порту. Для добавления других origins нужно расширить этот список.

**Health-check эндпоинт:**
```
GET /health → {"status": "ok"}
```
Не требует авторизации. Используется Docker для проверки готовности сервиса.

**Startup/shutdown-хуки:** логируют факт запуска/остановки приложения.

---

## 6. Ядро приложения — `core/`

### `core/config.py`

**Класс `Settings`** — singleton конфигурации. Использует `pydantic-settings` для чтения из `.env`-файла.

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    DATABASE_URL: str   # строка подключения к PostgreSQL
    SECRET_KEY: str     # ключ подписи JWT
```

Экспортирует глобальный инстанс `settings = Settings()`. Импортируется везде, где нужна конфигурация.

---

### `core/database.py`

Создаёт движок SQLAlchemy и фабрику сессий.

```python
engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
```

**`expire_on_commit=False`** — после `commit()` объекты не помечаются как "устаревшие". Это важно для async: повторный доступ к полям после commit не вызывает дополнительных SELECT-запросов.

**Класс `Base`** — базовый класс для всех ORM-моделей:
```python
class Base(DeclarativeBase):
    pass
```

**Зависимость `get_db()`** — создаёт AsyncSession на время одного HTTP-запроса:
```python
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```
Сессия автоматически закрывается после завершения запроса (context manager).

---

### `core/security.py`

Работа с паролями и JWT-токенами.

**Хеширование паролей** (bcrypt):
```python
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str      # → bcrypt-хеш
def verify_password(plain: str, hashed: str) # → bool
```

**JWT-токены** (PyJWT, алгоритм HS256):
```python
def create_token(user_id: str, role: str) -> str:
    return jwt.encode({"sub": user_id, "role": role}, settings.SECRET_KEY, algorithm="HS256")

def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
```

**Формат payload токена:**
```json
{"sub": "UUID пользователя", "role": "admin|vice_principal|teacher|student|parent"}
```

**Важно:** токены не имеют срока действия (`exp` не устанавливается). Токен действует вечно, пока не изменится `SECRET_KEY` или не деактивируется пользователь.

---

### `core/logger.py`

Настраивает два обработчика логов:
- **Файловый** (`RotatingFileHandler`): `/app/app/logs/api.log`, максимум 10 МБ, 5 архивных файлов
- **Консольный** (`StreamHandler`): вывод в stdout контейнера

Формат записи:
```
2026-06-07 12:00:00 | INFO     | api | сообщение
```

Экспортирует `logger = get_logger("api")`. Используется в `middleware.py` и `main.py`.

---

## 7. Модели ORM — `models/`

Все модели наследуют `Base` из `core/database.py`. Используют **SQLAlchemy 2.0 Mapped/mapped_column** синтаксис с аннотациями типов.

### `models/__init__.py`

Реэкспортирует все модели. Импортируется в `main.py` как `import app.models` — это гарантирует, что все модели зарегистрированы в `Base.metadata` до запуска приложения (необходимо для Alembic).

---

### `models/user.py`

**Таблица association (M:M):**
```python
parent_student = Table(
    "parent_student", Base.metadata,
    Column("parent_id", UUID, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("student_id", UUID, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)
```
Association-таблица для связи родитель↔ученик. Оба FK каскадируют удаление.

---

**Класс `User`** (таблица `users`):

| Поле | SQLAlchemy-тип | Python-тип | Описание |
|------|---------------|-----------|----------|
| `id` | `UUID(as_uuid=True)`, PK | `uuid.UUID` | `default=uuid.uuid4` |
| `email` | `String(255)`, unique | `str` | Уникальный, формат проверяется в DB CHECK |
| `password_hash` | `Text` | `str` | bcrypt-хеш, min length 60 |
| `role` | `SAEnum(...)` | `str` | `admin/vice_principal/teacher/student/parent` |
| `first_name` | `String(100)` | `str` | |
| `last_name` | `String(100)` | `str` | |
| `middle_name` | `String(100)`, nullable | `str \| None` | |
| `is_active` | `Boolean`, default `True` | `bool` | |
| `created_at` | `DateTime(timezone=True)` | `datetime` | `server_default=now()` |
| `updated_at` | `DateTime(timezone=True)` | `datetime` | Обновляется триггером |

**`SAEnum` с `create_type=False`** — ENUM-тип `user_role` создаётся в БД через `init.sql`, а не при запуске приложения. Это предотвращает ошибки при повторной инициализации.

**Relationships:**

| Атрибут | Тип | lazy | cascade | Описание |
|---------|-----|------|---------|----------|
| `teacher_profile` | `TeacherProfile \| None` | `selectin` | `all, delete-orphan` | 1:1, только для role=teacher |
| `student_profile` | `StudentProfile \| None` | `selectin` | `all, delete-orphan` | 1:1, только для role=student |
| `children` | `list[User]` | `selectin` | — | M:M через `parent_student`, только для role=parent |
| `parents` | `list[User]` | `selectin` | — | Обратная сторона `children` |

`cascade="all, delete-orphan"` на `teacher_profile` и `student_profile` означает: при удалении пользователя SQLAlchemy явно удаляет связанный профиль до удаления пользователя, предотвращая нарушение NOT NULL constraint.

---

**Класс `TeacherProfile`** (таблица `teacher_profiles`):

| Поле | Описание |
|------|----------|
| `id` | UUID PK |
| `user_id` | FK → `users.id` ON DELETE CASCADE, UNIQUE |
| `subject_id` | FK → `subjects.id` ON DELETE RESTRICT |
| `created_at`, `updated_at` | временные метки |

`ON DELETE RESTRICT` на `subject_id` означает: невозможно удалить предмет, пока хотя бы один учитель имеет его в профиле.

---

**Класс `StudentProfile`** (таблица `student_profiles`):

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID PK | |
| `user_id` | FK → `users.id` ON DELETE CASCADE, UNIQUE | |
| `date_of_birth` | `Mapped[date \| None]` | Python `date` объект, хранится в DB как DATE |
| `created_at`, `updated_at` | | |

**Важно:** `date_of_birth` объявлен как `Mapped[date | None]` — SQLAlchemy правильно маппит Python `date` на DB-тип `DATE`. asyncpg требует именно Python `date` объект (не строку). Pydantic в схемах принимает ISO-строку `"YYYY-MM-DD"` и автоматически парсит в `date`.

---

### `models/subject.py`

**Класс `Subject`** (таблица `subjects`):

| Поле | Описание |
|------|----------|
| `id` | UUID PK |
| `name` | `String(100)`, UNIQUE, кириллица+пробел+дефис |
| `created_at`, `updated_at` | |

Relationships:
- `teacher_profiles`: список `TeacherProfile` (lazy=selectin) — кто преподаёт этот предмет
- `lessons`: список `Lesson` (lazy=selectin) — уроки по этому предмету

---

### `models/class_.py`

**Класс `Class`** (таблица `classes`):

| Поле | Описание |
|------|----------|
| `id` | UUID PK |
| `name` | `String(10)`, формат `^[1-9][0-9]?[А-ЯЁ]$` (напр. `9А`, `11Б`) |
| `academic_year` | `SmallInteger` (2000–2100) |
| `created_at`, `updated_at` | |
| UNIQUE | `(name, academic_year)` |

Relationships (все `cascade="all, delete-orphan"`):
- `class_students`: список `ClassStudent`
- `teacher_classes`: список `TeacherClass`
- `lessons`: список `Lesson`

Каскад `delete-orphan` гарантирует: при удалении класса SQLAlchemy удаляет все связанные записи через ORM (не полагаясь на DB CASCADE), что корректно работает с `lazy="selectin"`.

---

**Класс `ClassStudent`** (таблица `class_students`):

| Поле | Описание |
|------|----------|
| `id` | UUID PK |
| `class_id` | FK → `classes.id` ON DELETE CASCADE |
| `student_id` | FK → `users.id` ON DELETE CASCADE |
| `academic_year` | SmallInteger (2000–2100) |
| `enrolled_at` | DATE, `server_default=CURRENT_DATE` |
| UNIQUE | `(student_id, academic_year)` — один ученик в одном классе за учебный год |

---

**Класс `TeacherClass`** (таблица `teacher_classes`):

| Поле | Описание |
|------|----------|
| `id` | UUID PK |
| `teacher_id` | FK → `users.id` ON DELETE CASCADE |
| `class_id` | FK → `classes.id` ON DELETE CASCADE |
| `created_at` | |
| UNIQUE | `(teacher_id, class_id)` |

---

### `models/lesson.py`

**Класс `Lesson`** (таблица `lessons`):

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID PK | |
| `class_id` | FK → `classes.id` ON DELETE CASCADE | |
| `teacher_id` | FK → `users.id` ON DELETE RESTRICT | нельзя удалить учителя, у которого есть уроки |
| `subject_id` | FK → `subjects.id` ON DELETE RESTRICT | нельзя удалить предмет с уроками |
| `date` | `Date` | |
| `topic` | `String(500)`, nullable | начинается с кириллицы |
| `created_at`, `updated_at` | | |

Relationships:
- `class_`: `Class` (back_populates)
- `teacher`: `User` (selectin)
- `subject`: `Subject` (back_populates)
- `grades`: `list[Grade]` (cascade="all, delete-orphan")
- `attendances`: `list[Attendance]` (cascade="all, delete-orphan")

**Computed properties** (не хранятся в DB, вычисляются в Python):
```python
@property
def subject_name(self) -> str | None   # возвращает self.subject.name
@property
def class_name(self) -> str | None     # возвращает self.class_.name
@property
def teacher_name(self) -> str | None   # возвращает "Фамилия Имя" учителя
```
Используются в `LessonResponse` для удобства фронтенда (не нужны дополнительные запросы).

---

### `models/grade.py`

**Класс `Grade`** (таблица `grades`):

| Поле | Описание |
|------|----------|
| `id` | UUID PK |
| `lesson_id` | FK → `lessons.id` ON DELETE CASCADE |
| `student_id` | FK → `users.id` ON DELETE CASCADE |
| `value` | `SmallInteger` (1–5) |
| `comment` | `Text`, nullable |
| `created_at`, `updated_at` | |
| UNIQUE | `(lesson_id, student_id)` — одна оценка на пару (ученик, урок) |

---

### `models/attendance.py`

**Класс `Attendance`** (таблица `attendances`):

| Поле | Описание |
|------|----------|
| `id` | UUID PK |
| `lesson_id` | FK → `lessons.id` ON DELETE CASCADE |
| `student_id` | FK → `users.id` ON DELETE CASCADE |
| `status` | `SAEnum("present","absent","late","excused", create_type=False)`, default "present" |
| `created_at`, `updated_at` | |
| UNIQUE | `(lesson_id, student_id)` |

`create_type=False` — ENUM `attendance_status` создаётся в `init.sql`, не при запуске приложения.

---

### `models/notification.py`

**Класс `Notification`** (таблица `notifications`):

| Поле | Описание |
|------|----------|
| `id` | UUID PK |
| `recipient_id` | FK → `users.id` ON DELETE CASCADE |
| `title` | `String(255)` |
| `body` | `Text` |
| `is_read` | `Boolean`, default `False` |
| `created_at` | — нет `updated_at`, уведомления не редактируются |

---

## 8. Pydantic-схемы — `schemas/`

Схемы отвечают за:
- **Валидацию входных данных** (Create/Update)
- **Сериализацию ответов** (Response)

Все Response-схемы имеют `model_config = ConfigDict(from_attributes=True)` — позволяет создавать схему из ORM-объекта.

### `schemas/user.py`

**`UserShort`** — краткое представление пользователя (используется в связях):
```
id, first_name, last_name, middle_name, role
```

**`TeacherProfileCreate`**: `subject_id: uuid.UUID`

**`TeacherProfileUpdate`**: `subject_id: uuid.UUID | None`

**`TeacherProfileResponse`**: `id, user_id, subject_id, created_at, updated_at`

**`StudentProfileCreate`**: `date_of_birth: date | None`

**`StudentProfileUpdate`**: `date_of_birth: date | None`

**`StudentProfileResponse`**: `id, user_id, date_of_birth, created_at, updated_at`

**`UserCreate`**:
```
email: EmailStr
password: str (8–128 символов)
role: "admin"|"vice_principal"|"teacher"|"student"|"parent"
first_name: str (2–100, ^[А-ЯЁ][а-яё\-]+$)
last_name: str (2–100, ^[А-ЯЁ][а-яё\-]+$)
middle_name: str | None (2–100, ^[А-ЯЁ][а-яё]+$, без дефиса)
```
Валидаторы `first_name`/`last_name`/`middle_name` проверяют кириллический формат через `field_validator`.

**`UserUpdate`**: все поля опциональны, те же правила.

**`UserResponse`**:
```
id, email, role, first_name, last_name, middle_name, is_active,
created_at, updated_at,
teacher_profile: TeacherProfileResponse | None,
student_profile: StudentProfileResponse | None,
children: list[UserShort]
```

---

### `schemas/subject.py`

**`SubjectCreate`**: `name: str` (2–100, `^[А-ЯЁа-яё][А-ЯЁа-яё\s\-]+$`)

**`SubjectUpdate`**: `name: str | None`

**`SubjectResponse`**: `id, name, created_at, updated_at`

---

### `schemas/class_.py`

**`ClassCreate`**:
```
name: str (2–4 символа, ^[1-9][0-9]?[А-ЯЁ]$, например "9А", "11Б")
academic_year: int (2000–2100)
```

**`ClassUpdate`**: все поля опциональны.

**`ClassResponse`**: `id, name, academic_year, created_at, updated_at`

**`ClassStudentCreate`**:
```
class_id: uuid.UUID
student_id: uuid.UUID
academic_year: int (2000–2100)
enrolled_at: date | None
```

**`StudentShort`**: `id, first_name, last_name, email` (для отображения в списке учеников класса)

**`ClassStudentResponse`**: `id, class_id, student_id, academic_year, enrolled_at, student: StudentShort | None`

**`TeacherClassCreate`**: `teacher_id: uuid.UUID, class_id: uuid.UUID`

**`TeacherClassResponse`**: `id, teacher_id, class_id, created_at`

**`ParentStudentCreate`**: `parent_id: uuid.UUID, student_id: uuid.UUID`

**`ParentStudentResponse`**: `parent_id, student_id`

---

### `schemas/lesson.py`

**`LessonCreate`**:
```
class_id, teacher_id, subject_id: uuid.UUID
date: date
topic: str | None (2–500, ^[А-ЯЁа-яё].*)
```

**`LessonUpdate`**: `date: date | None`, `topic: str | None`

**`LessonResponse`**: `id, class_id, teacher_id, subject_id, date, topic, created_at, updated_at,
subject_name, class_name, teacher_name` — последние три заполняются из ORM-свойств модели Lesson.

---

### `schemas/grade.py`

**`GradeCreate`**: `lesson_id, student_id: uuid.UUID`, `value: int (1–5)`, `comment: str | None (2–1000)`

**`GradeUpdate`**: `value: int | None`, `comment: str | None`

**`GradeResponse`**: `id, lesson_id, student_id, value, comment, created_at, updated_at`

---

### `schemas/attendance.py`

**`AttendanceStatus`** = `Literal["present", "absent", "late", "excused"]`

**`AttendanceCreate`**: `lesson_id, student_id: uuid.UUID`, `status: AttendanceStatus = "present"`

**`AttendanceUpdate`**: `status: AttendanceStatus | None`

**`AttendanceResponse`**: `id, lesson_id, student_id, status, created_at, updated_at`

---

### `schemas/notification.py`

**`NotificationCreate`**: `recipient_id: uuid.UUID`, `title: str (2–255)`, `body: str (2–5000)`

**`NotificationResponse`**: `id, recipient_id, title, body, is_read, created_at`

---

## 9. Зависимости — `dependencies.py`

**Файл:** `backend/app/dependencies.py`

### `get_current_user`

Зависимость FastAPI — проверяет JWT-токен и возвращает текущего пользователя.

```python
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: AsyncSession = Depends(get_db),
) -> User:
```

**Алгоритм:**
1. Извлекает Bearer-токен из заголовка `Authorization`
2. Вызывает `decode_token(token)` — декодирует JWT
3. Получает `user_id = payload["sub"]`
4. Выполняет SELECT пользователя по ID с `selectinload(teacher_profile, student_profile, children)`
5. Проверяет `user.is_active`
6. Возвращает ORM-объект `User` с загруженными relationships

При отсутствии заголовка `Authorization` FastAPI автоматически возвращает **403** (поведение `HTTPBearer()` по умолчанию).

При невалидном токене — **401** `"Недействительный токен"`.

При неактивном пользователе — **401** `"Пользователь не найден или неактивен"`.

---

### `require_role(*roles)`

Фабрика зависимостей — создаёт зависимость проверки роли:

```python
def require_role(*roles: str):
    async def _check(current_user=Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="Недостаточно прав")
        return current_user
    return _check
```

**Использование в роутерах:**
```python
_ADMIN    = require_role("admin")
_ADMIN_VP = require_role("admin", "vice_principal")
_ADMIN_VP_TEACHER = require_role("admin", "vice_principal", "teacher")
```

Зависимость возвращает аутентифицированного пользователя с нужной ролью. Роутеры используют `_: User = Depends(_ADMIN)` когда пользователь не нужен в теле хендлера, или `current_user: User = Depends(...)` когда нужен.

---

## 10. Middleware — `middleware.py`

**Класс `LoggingMiddleware`** — логирует все HTTP-запросы.

**Для каждого запроса:**
1. Генерируется 8-символьный `request_id` (первые 8 символов UUID)
2. Логируется входящий запрос: `[req_id] → METHOD /path?query`
3. Выполняется обработчик (`call_next`)
4. Логируется ответ: `[req_id] ← STATUS METHOD /path (время_мс)`
   - `INFO` для 1xx–3xx
   - `WARNING` для 4xx–5xx
5. При необработанном исключении логируется полный traceback

Пример лога:
```
2026-06-07 12:00:00 | INFO    | api | [a1b2c3d4] → POST /auth/login
2026-06-07 12:00:00 | INFO    | api | [a1b2c3d4] ← 200 POST /auth/login (12.3ms)
2026-06-07 12:00:01 | WARNING | api | [e5f6g7h8] ← 401 POST /auth/login (5.1ms)
```

---

## 11. Роутеры — `routers/`

### `routers/auth.py` — `POST /auth/login`

**Prefix:** `/auth`

| Метод | Путь | Auth | Тело запроса | Ответ |
|-------|------|------|-------------|-------|
| POST | `/auth/login` | — | `username` + `password` (form-data) | `access_token, token_type, role, user_id` |

**Алгоритм:**
1. Ищет пользователя по `email` (`form.username`)
2. Проверяет `verify_password(form.password, user.password_hash)`
3. Проверяет `user.is_active`
4. Возвращает JWT через `create_token(user_id, role)`

**Важно:** принимает `application/x-www-form-urlencoded` (OAuth2 стандарт), а не JSON. Поле называется `username`, но содержит email.

---

### `routers/users.py` — `/users`

**Prefix:** `/users`

Вспомогательные функции:
- `_user_opts()` — список `selectinload` опций (teacher_profile, student_profile, children) для полной загрузки пользователя
- `_get_user_full(db, user_id)` — SELECT пользователя с полными связями

| Метод | Путь | Доступ | Описание |
|-------|------|--------|----------|
| GET | `/users/` | admin, vp, teacher | Список пользователей. Учитель видит только студентов/родителей своих классов |
| GET | `/users/me` | все | Текущий пользователь |
| GET | `/users/{id}` | all (себя), admin/vp (любого) | Пользователь по ID |
| POST | `/users/` | admin, vp | Создать пользователя. VP не может создавать admin |
| PATCH | `/users/{id}` | admin (любого), vp (только себя), остальные (только себя) | Обновить. VP не может менять `role` и `is_active` |
| DELETE | `/users/{id}` | admin | Удалить |

**Профиль учителя:**

| Метод | Путь | Доступ | Описание |
|-------|------|--------|----------|
| POST | `/users/{id}/teacher-profile` | admin, vp | Создать. Требует `role=teacher`. 409 если уже есть |
| PATCH | `/users/{id}/teacher-profile` | admin, vp | Обновить `subject_id` |

**Профиль ученика:**

| Метод | Путь | Доступ | Описание |
|-------|------|--------|----------|
| POST | `/users/{id}/student-profile` | admin, vp | Создать. Требует `role=student`. 409 если уже есть |
| PATCH | `/users/{id}/student-profile` | admin, vp | Обновить `date_of_birth` |

**Связь родитель–ребёнок:**

| Метод | Путь | Доступ | Описание |
|-------|------|--------|----------|
| POST | `/users/parents/{parent_id}/children/{student_id}` | admin, vp | Привязать. 409 если связь уже есть |
| DELETE | `/users/parents/{parent_id}/children/{student_id}` | admin, vp | Удалить связь |

---

### `routers/subjects.py` — `/subjects`

| Метод | Путь | Доступ | Описание |
|-------|------|--------|----------|
| GET | `/subjects/` | все (auth) | Список предметов, отсортированный по имени |
| GET | `/subjects/{id}` | все (auth) | Предмет по ID. 404 если нет |
| POST | `/subjects/` | admin, vp | Создать. 409 при дублировании имени |
| PATCH | `/subjects/{id}` | admin, vp | Обновить имя. 409 при конфликте |
| DELETE | `/subjects/{id}` | admin, vp | Удалить. 409 если предмет используется (teacher_profile или lesson) |

---

### `routers/classes.py` — `/classes`

**Зависимости:**
```python
_ADMIN    = require_role("admin")
_ADMIN_VP = require_role("admin", "vice_principal")
_ADMIN_VP_TEACHER = require_role("admin", "vice_principal", "teacher")
```

**CRUD классов:**

| Метод | Путь | Доступ | Описание |
|-------|------|--------|----------|
| GET | `/classes/` | admin, vp, teacher | Список. Учитель видит только свои классы (через teacher_classes) |
| GET | `/classes/{id}` | admin, vp, teacher | Класс по ID |
| POST | `/classes/` | admin, vp | Создать. 409 при дублировании `(name, academic_year)` |
| PATCH | `/classes/{id}` | admin, vp | Обновить |
| DELETE | `/classes/{id}` | **admin only** | Удалить |

**Управление учениками в классе:**

| Метод | Путь | Доступ | Описание |
|-------|------|--------|----------|
| GET | `/classes/{id}/students` | admin, vp, teacher | Список учеников класса |
| POST | `/classes/{id}/students` | admin, vp | Добавить ученика. 409 если ученик уже в классе в том же году |
| DELETE | `/classes/{id}/students/{student_id}` | admin, vp | Удалить ученика из класса |

**Управление учителями в классе:**

| Метод | Путь | Доступ | Описание |
|-------|------|--------|----------|
| GET | `/classes/{id}/teachers` | admin, vp, teacher | Список учителей класса |
| POST | `/classes/{id}/teachers` | admin, vp | Прикрепить учителя. 409 если уже прикреплён |
| DELETE | `/classes/{id}/teachers/{teacher_id}` | admin, vp | Открепить учителя |

---

### `routers/lessons.py` — `/lessons`

Вспомогательная функция `_assert_teacher_owns_class(teacher_id, class_id, db)` — проверяет, что учитель прикреплён к классу через `teacher_classes`. Если нет — 403.

| Метод | Путь | Доступ | Описание |
|-------|------|--------|----------|
| GET | `/lessons/` | все (auth) | Список с фильтром `?class_id=UUID`. Учитель видит свои уроки, ученик — уроки своих классов, родитель — уроки классов детей |
| GET | `/lessons/{id}` | все (auth) | Урок по ID. Учитель не видит чужие уроки (403) |
| POST | `/lessons/` | admin, vp | Создать урок. Если учитель создаёт сам — проверяется принадлежность к классу |
| PATCH | `/lessons/{id}` | admin, vp, teacher | Обновить. Учитель может менять только `topic` (не `date`) |
| DELETE | `/lessons/{id}` | admin, vp | Удалить |

---

### `routers/grades.py` — `/grades`

Вспомогательная функция `_assert_teacher_controls_lesson(teacher_id, lesson, db)` — проверяет, что учитель ведёт класс этого урока.

| Метод | Путь | Доступ | Описание |
|-------|------|--------|----------|
| GET | `/grades/` | все (auth) | Список с фильтрами `?lesson_id`, `?student_id`. Каждая роль видит только своё |
| GET | `/grades/{id}` | все (auth) | Оценка по ID с проверкой прав |
| POST | `/grades/` | admin, vp, teacher | Выставить оценку. Проверяется: ученик в классе урока. 409 при дубле |
| PATCH | `/grades/{id}` | admin, vp, teacher | Изменить оценку/комментарий |
| DELETE | `/grades/{id}` | admin, vp, teacher | Удалить |

**Фильтрация по ролям в GET `/grades/`:**
- `student` — только свои оценки
- `parent` — оценки всех детей
- `teacher` — оценки в уроках своих классов
- `admin`, `vp` — все оценки

---

### `routers/attendances.py` — `/attendances`

Аналогична структуре `grades.py`.

| Метод | Путь | Доступ | Описание |
|-------|------|--------|----------|
| GET | `/attendances/` | все (auth) | Список с фильтрами `?lesson_id`, `?student_id` |
| GET | `/attendances/{id}` | все (auth) | Запись по ID |
| POST | `/attendances/` | admin, vp, teacher | Отметить посещаемость. 409 при дубле |
| PATCH | `/attendances/{id}` | admin, vp, teacher | Изменить статус |
| DELETE | `/attendances/{id}` | admin, vp, teacher | Удалить |

**Статусы:** `present` (присутствовал), `absent` (отсутствовал), `late` (опоздал), `excused` (уважительная причина)

---

### `routers/notifications.py` — `/notifications`

| Метод | Путь | Доступ | Описание |
|-------|------|--------|----------|
| GET | `/notifications/` | все (auth) | Уведомления текущего пользователя. `?unread_only=true` — только непрочитанные |
| GET | `/notifications/{id}` | владелец + admin | По ID |
| POST | `/notifications/` | admin, vp, teacher | Создать уведомление любому получателю |
| PATCH | `/notifications/{id}/read` | владелец | Пометить прочитанным (идемпотентно) |
| DELETE | `/notifications/{id}` | владелец + admin | Удалить |

---

## 12. Схема авторизации

```
Клиент
  │
  ├─ POST /auth/login (form: username, password)
  │       │
  │       └─ Ответ: {access_token, token_type: "bearer", role, user_id}
  │
  ├─ Все остальные запросы:
  │   Header: Authorization: Bearer <access_token>
  │       │
  │       └─ HTTPBearer() извлекает токен
  │               │
  │               └─ get_current_user():
  │                       1. decode_token() → {sub: uuid, role: string}
  │                       2. SELECT users WHERE id = uuid
  │                       3. Проверка is_active
  │                       4. Возврат User ORM-объекта
  │
  └─ require_role("admin", ...):
          │
          └─ Проверка user.role in allowed_roles
                  ├─ Да → передать user в хендлер
                  └─ Нет → 403 Недостаточно прав
```

**Матрица прав по ролям:**

| Операция | admin | vice_principal | teacher | student | parent |
|----------|-------|---------------|---------|---------|--------|
| Создание пользователей | ✓ | ✓ (не admin) | — | — | — |
| Удаление пользователей | ✓ | — | — | — | — |
| CRUD предметов | ✓ | ✓ | — | — | — |
| CRUD классов | ✓ | ✓ | — (только просмотр своих) | — | — |
| Управление учениками/учителями в классах | ✓ | ✓ | — | — | — |
| Создание уроков | ✓ | ✓ | — | — | — |
| Редактирование уроков | ✓ | ✓ | только тему | — | — |
| Оценки/посещаемость (запись) | ✓ | ✓ | ✓ (своих классов) | — | — |
| Просмотр оценок/посещаемости | ✓ | ✓ | ✓ (своих) | ✓ (своих) | ✓ (детей) |
| Отправка уведомлений | ✓ | ✓ | ✓ | — | — |

---

## 13. Жизненный цикл HTTP-запроса

На примере `PATCH /grades/uuid`:

```
1. Nginx (frontend-контейнер) проксирует на порт 8000

2. uvicorn принимает HTTP-запрос

3. CORSMiddleware проверяет Origin

4. LoggingMiddleware:
   - генерирует request_id
   - логирует "→ PATCH /grades/uuid"

5. FastAPI routing → router grades.py → update_grade()

6. FastAPI выполняет Depends:
   a. get_db() → создаёт AsyncSession
   b. HTTPBearer() → извлекает токен из заголовка
   c. get_current_user() → декодирует JWT, загружает User из DB
   d. require_role("teacher","admin","vp") → проверяет роль

7. FastAPI парсит тело запроса через GradeUpdate (Pydantic)
   → ValidationError → 422 если данные невалидны

8. Выполняется тело хендлера update_grade():
   a. db.get(Grade, grade_id) → SELECT grades WHERE id=?
   b. Проверка прав (если teacher — проверка принадлежности к классу)
   c. setattr(grade, field, value) для каждого поля
   d. await db.commit() → UPDATE grades SET ... WHERE id=?
   e. await db.refresh(grade) → обновляет объект из DB
   f. return grade → FastAPI сериализует через GradeResponse

9. LoggingMiddleware логирует "← 200 PATCH /grades/uuid (Xms)"

10. AsyncSession закрывается (context manager get_db())
```

---

## 14. Каскады удаления ORM

Все критически важные цепочки удаления используют **ORM-cascade** (`cascade="all, delete-orphan"`) для корректной работы с `lazy="selectin"`.

**Проблема:** `lazy="selectin"` загружает дочерние объекты в SQLAlchemy-сессию при запросе родителя. Без явного cascade ORM пытается SET NULL на FK-полях дочерних объектов, что нарушает NOT NULL-ограничения → 500.

**Решение:** `cascade="all, delete-orphan"` → ORM явно удаляет дочерние объекты до удаления родителя.

```
DELETE User (teacher)
  └─ cascade → DELETE TeacherProfile    [cascade="all, delete-orphan"]
       └─ subjects.id ON DELETE RESTRICT (не затрагивает Subject)

DELETE User (student)
  └─ cascade → DELETE StudentProfile   [cascade="all, delete-orphan"]

DELETE Class
  ├─ cascade → DELETE ClassStudent[]   [cascade="all, delete-orphan"]
  ├─ cascade → DELETE TeacherClass[]   [cascade="all, delete-orphan"]
  └─ cascade → DELETE Lesson[]         [cascade="all, delete-orphan"]
       ├─ cascade → DELETE Grade[]     [cascade="all, delete-orphan"]
       └─ cascade → DELETE Attendance[]  [cascade="all, delete-orphan"]
```

**DB-уровневые CASCADE** (PostgreSQL):
- `teacher_profiles.user_id ON DELETE CASCADE` — резервный механизм
- `class_students.class_id ON DELETE CASCADE`
- `grades.lesson_id ON DELETE CASCADE`
- и т.д.

Оба механизма (ORM + DB) дополняют друг друга и обеспечивают целостность данных.

---

## 15. Утилиты

### `seed_admin.py`

Скрипт для создания первого администратора. Использует `asyncpg` напрямую (не через SQLAlchemy).

**Запуск:**
```bash
docker compose exec api python seed_admin.py
```

**Данные по умолчанию:**
```
Email:    admin@admin.com
Password: 1234
```

Скрипт проверяет, что пользователь с таким email не существует, и создаёт его с ролью `admin`.

---

### `migrations/env.py`

Конфигурация Alembic для асинхронных миграций. Настроен для работы с `create_async_engine`. В проекте используется `sql/init.sql` для инициализации схемы вместо Alembic-миграций. Alembic подготовлен для будущих изменений схемы.

**Для генерации миграции:**
```bash
docker compose exec api alembic revision --autogenerate -m "описание"
docker compose exec api alembic upgrade head
```

---

### Документация API (Swagger)

FastAPI автоматически генерирует OpenAPI-документацию:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **OpenAPI JSON:** `http://localhost:8000/openapi.json`

Все эндпоинты, схемы запросов и ответов, коды ошибок описаны автоматически на основе аннотаций и `response_model`.
