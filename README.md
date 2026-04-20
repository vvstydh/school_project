# Электронный школьный журнал

> _[Краткое описание проекта — что это, для кого, какую задачу решает]_

---

## Стек технологий

| Слой | Технология |
|---|---|
| Backend | FastAPI, Python 3.12 |
| ORM | SQLAlchemy 2.0 (async) |
| База данных | PostgreSQL 16 |
| Аутентификация | JWT (HS256) |
| Контейнеризация | Docker, Docker Compose |

---

## Требования

- Docker `>= XX.X`
- Docker Compose `>= X.X`
- _[другие требования если есть]_

---

## Быстрый старт

### 1. Клонировать репозиторий

```bash
# вставь команду клонирования
git clone <https://github.com/vvstydh/school_project.git> && cd <папка>
```

### 2. Создать файл окружения

```bash
# скопировать пример
cp .env.example .env
```

Открыть `.env` и заполнить переменные:

```env
POSTGRES_DB=school
POSTGRES_USER=postgres
POSTGRES_PASSWORD=        # вставь свой пароль
POSTGRES_PORT=5434

DATABASE_URL=postgresql+asyncpg://postgres:<пароль>@db:5432/school
SECRET_KEY=               # минимум 32 символа, любая случайная строка
```

### 3. Запустить контейнеры

```bash
# вставь команду запуска
docker compose up -d
```

### 4. Создать первого администратора

```bash
# скопировать скрипт в контейнер
docker cp backend/seed_admin.py school_journal_api:/app/seed_admin.py

# запустить
docker compose exec api python seed_admin.py
```

После выполнения в консоли появится:
```
Администратор создан: admin@admin.com / 1234
```

### 5. Проверить что всё работает

```bash
curl http://localhost:8000/health
# ожидаемый ответ: {"status":"ok"}
```

---

## Подключение к Swagger

После запуска контейнеров открыть в браузере:

```
http://localhost:8000/docs
```

Альтернативный интерфейс ReDoc:

```
http://localhost:8000/redoc
```

---

## Тестирование API

### Шаг 1 — Получить токен

**Через curl:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@admin.com&password=1234"
```

**Через Swagger:**
1. Открыть `http://localhost:8000/docs`
2. Нажать кнопку **Authorize** (в правом верхнем углу)
3. Ввести `username` и `password`
4. Нажать **Authorize**

Все последующие запросы в Swagger будут автоматически отправляться с токеном.

---

### Шаг 2 — Использовать токен в curl

```bash
# сохранить токен в переменную
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@admin.com&password=1234" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# пример запроса с токеном
curl http://localhost:8000/users/me \
  -H "Authorization: Bearer $TOKEN"
```

---

### Примеры запросов

#### Создать пользователя
```bash
curl -X POST http://localhost:8000/users/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "",
    "password": "",
    "role": "",
    "first_name": "",
    "last_name": "",
    "middle_name": ""
  }'
```

#### Создать предмет
```bash
curl -X POST http://localhost:8000/subjects/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": ""}'
```

#### Создать класс
```bash
curl -X POST http://localhost:8000/classes/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "",
    "academic_year": 
  }'
```

#### Выставить оценку
```bash
curl -X POST http://localhost:8000/grades/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "lesson_id": "",
    "student_id": "",
    "value": ,
    "comment": ""
  }'
```

---

## Роли и доступ

| Роль | Возможности |
|---|---|
| `admin` | Полный доступ ко всем эндпоинтам |
| `vice_principal` | Просмотр всех данных, управление классами |
| `teacher` | CRUD оценок и посещаемости в своих классах |
| `student` | Просмотр своих оценок, посещаемости, уведомлений |
| `parent` | Просмотр данных своих детей и своих уведомлений |

---

## Структура проекта

```
school_project/
├── backend/
│   ├── app/
│   │   ├── core/          # config, database, security
│   │   ├── models/        # SQLAlchemy ORM модели
│   │   ├── schemas/       # Pydantic схемы
│   │   ├── routers/       # эндпоинты
│   │   ├── dependencies.py
│   │   └── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── sql/
│   └── init.sql           # схема БД
├── docker-compose.yml
└── .env
```

---

## Полезные команды

```bash
# посмотреть логи api
docker compose logs api -f

# перезапустить api
docker compose restart api

# зайти в контейнер
docker compose exec api bash

# зайти в PostgreSQL
docker compose exec db psql -U postgres -d school

# остановить все контейнеры
docker compose down

# остановить и удалить данные БД
docker compose down -v
```

---

## Авторы

| Имя | Роль |
|---|---|
| | |
