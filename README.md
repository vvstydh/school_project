# Электронный школьный журнал

## Быстрый старт

### 1. Клонировать репозиторий

```bash
git clone <https://github.com/vvstydh/school_project.git> && cd <папка>
```

### 2. Создать файл окружения

```bash
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
# запуск всех контейнеров
docker compose up -d

# запуск контейнера с БД
docker compose up -d db

# запуск контейнера с API
docker compose up -d api

# перезапуск API после изменений
docker compose up -d --build api

# остановить все контейнеры
docker compose down

# остановить и удалить данные БД
docker compose down -v
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

---

## Тестирование API

### Шаг 1 — Получить токен

**Через curl получить токен:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@admin.com&password=1234"
```

### Шаг 2 — Использование токена

**После получения токена в Swagger:**
1. Открыть `http://localhost:8000/docs`
2. Нажать кнопку **Authorize** (в правом верхнем углу)
3. Ввести `token`
4. Нажать **Authorize**

Все последующие запросы в Swagger будут автоматически отправляться с токеном.
