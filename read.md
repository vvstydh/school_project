# Электронный школьный журнал

Веб-приложение для управления школьным журналом: оценки, посещаемость, расписание уроков, уведомления. Одна школа, без мультитенантности.

## Запуск

```bash
docker compose up -d --build   # первый запуск или после изменений в frontend/
docker compose up -d           # если менялся только backend/ (volume mount)
docker compose restart frontend  # НЕ применяет изменения файлов (файлы baked in образ)
```

- **API:** http://localhost:8000 — документация Swagger на `/docs`
- **Frontend:** http://localhost:80

## Стек

| Слой | Технологии |
|------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 async, Pydantic v2, asyncpg |
| Auth | PyJWT HS256, bcrypt (passlib), JWT без срока действия |
| БД | PostgreSQL 16 (Docker), схема в `sql/init.sql` |
| Frontend | Vanilla JS, AdminLTE 3, Bootstrap 5, Font Awesome 6 |
| Deploy | Docker Compose (3 сервиса: db, api, frontend/nginx) |

## Структура проекта

```
school_project/
├── docker-compose.yml
├── sql/
│   └── init.sql              # Полная схема БД (таблицы, ENUM, ограничения)
├── backend/
│   ├── Dockerfile
│   ├── app/
│   │   ├── main.py           # FastAPI app, подключение роутеров, CORS
│   │   ├── dependencies.py   # get_current_user, require_role
│   │   ├── middleware.py     # Логирование запросов
│   │   ├── core/
│   │   │   ├── config.py     # Settings (pydantic-settings, .env)
│   │   │   ├── database.py   # async engine, AsyncSession, get_db
│   │   │   ├── security.py   # create_token, verify_password, hash_password
│   │   │   └── logger.py     # Настройка логирования
│   │   ├── models/           # SQLAlchemy ORM (Mapped[], mapped_column())
│   │   │   ├── user.py       # User, TeacherProfile, StudentProfile, parent_student
│   │   │   ├── class_.py     # Class, ClassStudent, TeacherClass
│   │   │   ├── subject.py    # Subject
│   │   │   ├── lesson.py     # Lesson (+ @property: subject_name, class_name, teacher_name)
│   │   │   ├── grade.py      # Grade
│   │   │   ├── attendance.py # Attendance
│   │   │   └── notification.py # Notification
│   │   ├── schemas/          # Pydantic v2 (Create / Update / Response)
│   │   │   ├── user.py       # field_validator для рус. имён (не pattern=)
│   │   │   ├── class_.py     # field_validator для формата названия класса
│   │   │   ├── lesson.py     # LessonResponse включает subject_name, class_name, teacher_name
│   │   │   └── ...
│   │   └── routers/          # FastAPI роутеры (prefix + tags на каждом)
│   │       ├── auth.py       # POST /auth/login → JWT
│   │       ├── users.py      # CRUD /users/ + профили + связь родитель-ребёнок
│   │       ├── subjects.py   # CRUD /subjects/
│   │       ├── classes.py    # CRUD /classes/ + ученики + учителя
│   │       ├── lessons.py    # CRUD /lessons/ (фильтрация по роли)
│   │       ├── grades.py     # CRUD /grades/ (фильтрация по роли)
│   │       ├── attendances.py # CRUD /attendances/ (фильтрация по роли)
│   │       └── notifications.py # CRUD /notifications/
└── frontend/
    ├── Dockerfile            # nginx:alpine, COPY . /usr/share/nginx/html
    ├── nginx.conf
    ├── css/custom.css        # Переопределения Bootstrap/AdminLTE
    ├── js/
    │   ├── api.js            # fetch-обёртка, форматирование ошибок Pydantic → рус.
    │   ├── auth.js           # login(), logout(), redirectByRole()
    │   ├── guards.js         # requireAuth(...roles)
    │   └── pages/
    │       ├── admin/common.js    # loadAdminComponents, showAlert, ROLE_LABELS
    │       ├── teacher/common.js  # loadTeacherComponents, GRADE_COLORS, ATTENDANCE_LABELS
    │       ├── student/common.js  # loadStudentComponents
    │       ├── parent/common.js   # loadParentComponents
    │       └── vice_principal/common.js
    ├── components/
    │   ├── navbar.html
    │   ├── sidebar-admin.html
    │   ├── sidebar-teacher.html
    │   ├── sidebar-student.html
    │   ├── sidebar-parent.html
    │   └── sidebar-vp.html
    └── pages/
        ├── login.html
        ├── admin/
        │   ├── dashboard.html
        │   ├── users/index.html, create.html, edit.html
        │   ├── classes/index.html, create.html, edit.html, detail.html
        │   ├── subjects/index.html
        │   ├── lessons/index.html
        │   ├── grades/index.html
        │   ├── attendances/index.html
        │   └── notifications/index.html
        ├── vice_principal/
        │   ├── dashboard.html
        │   └── users/index.html, create.html, edit.html, profile.html, view.html
        ├── teacher/
        │   ├── dashboard.html
        │   ├── lessons/index.html, detail.html
        │   ├── grades/index.html
        │   ├── attendances/index.html
        │   └── notifications.html       # + отправка родителям и отмена уроков
        ├── student/
        │   ├── dashboard.html
        │   ├── lessons.html
        │   ├── grades.html
        │   ├── attendances.html
        │   ├── notifications.html
        │   └── analytics.html           # KPI + по предметам + четверти + посещаемость
        └── parent/
            ├── dashboard.html
            ├── grades.html
            ├── attendances.html
            └── notifications.html
```

## База данных

### Таблицы

| Таблица | Описание |
|---------|----------|
| `users` | Все пользователи, role ENUM |
| `teacher_profiles` | 1:1 к users, subject_id |
| `student_profiles` | 1:1 к users, date_of_birth, record_number |
| `parent_student` | M:M родитель ↔ ученик |
| `subjects` | Предметы |
| `classes` | Классы (name + academic_year) |
| `class_students` | M:M класс ↔ ученик + academic_year |
| `teacher_classes` | M:M учитель ↔ класс |
| `lessons` | Урок (class_id, teacher_id, subject_id, date, topic) |
| `grades` | Оценка (lesson_id, student_id, value 1–5, comment) |
| `attendances` | Посещаемость (lesson_id, student_id, status ENUM) |
| `notifications` | Уведомление (recipient_id, title, body, is_read) |

### ENUM типы
- `user_role`: `admin` | `vice_principal` | `teacher` | `student` | `parent`
- `attendance_status`: `present` | `absent` | `late` | `excused`

### Ключевые ограничения
- `UNIQUE(lesson_id, student_id)` в grades и attendances
- `UNIQUE(student_id, academic_year)` в class_students
- `UNIQUE(teacher_id, class_id)` в teacher_classes
- Имя/фамилия: `^[А-ЯЁ][а-яё\-]+$`, отчество: `^[А-ЯЁ][а-яё]+$`
- Название класса: `^[1-9][0-9]?[А-ЯЁ]$` (например `1В`, `10А`)
- Оценка: 1–5, дата урока: 2000-01-01 .. сегодня+1 год

## Роли и доступ

| Роль | Что может |
|------|-----------|
| `admin` | Полный CRUD всего |
| `vice_principal` | CRUD классов/расписания, просмотр всего, редактирование только своего профиля |
| `teacher` | Просмотр своих уроков, CRUD оценок/посещаемости в своих классах, отправка уведомлений родителям и ученикам |
| `student` | Просмотр своих уроков/оценок/посещаемости/уведомлений, аналитика |
| `parent` | Просмотр данных своих детей (оценки, посещаемость), свои уведомления |

## Аутентификация

- `POST /auth/login` принимает form-data (`username`, `password`), возвращает `access_token`
- JWT HS256, без срока действия, payload: `{ "sub": "<uuid>", "role": "<role>" }`
- Токен хранится в `sessionStorage` (не localStorage)
- 401 → redirect на `/pages/login.html`, 403 → redirect на `/pages/login.html`

## API — ключевые особенности

### Фильтрация по роли в GET-запросах
- `GET /lessons/` — teacher видит только свои уроки, student только уроки своего класса, parent только уроки классов своих детей
- `GET /grades/` — student видит только свои, parent только детей, teacher только своих классов
- `GET /attendances/` — аналогично grades

### LessonResponse
Содержит computed-поля через `@property` на модели:
- `subject_name` — имя предмета
- `class_name` — название класса
- `teacher_name` — «Фамилия Имя» учителя

### Валидация ошибок
Pydantic `field_validator` используется вместо `pattern=` в Field — чтобы сообщения об ошибках были на русском. `api.js` форматирует массив ошибок Pydantic в «Поле: сообщение» с маппингом поля на русское название.

## Frontend — ключевые особенности

### Загрузка компонентов
Каждая страница загружает navbar и sidebar через fetch:
```js
await loadAdminComponents('activePage'); // в common.js каждой роли
```

### Константы (в common.js каждой роли)
```js
const GRADE_COLORS = { 5: 'success', 4: 'info', 3: 'warning', 2: 'danger', 1: 'danger' };
const ATTENDANCE_LABELS = {
    present: { label: 'Присутствовал', color: 'success' },
    absent:  { label: 'Отсутствовал',  color: 'danger' },
    late:    { label: 'Опоздал',        color: 'warning' },
    excused: { label: 'Уважительная',  color: 'info' },
};
```

### Важно: rebuild frontend
Файлы копируются в образ при `docker build`. `docker compose restart frontend` **не** применяет изменения файлов. Нужен `docker compose up -d --build frontend`.

### Уведомления — верстка
Для корректного переноса длинного текста используются CSS-классы:
- `.notif-text` — `min-width: 0; overflow: hidden` на flex-item контейнере текста
- `.notif-title` — `min-width: 0; word-break: break-word` на заголовке (сам flex-item)
- `.notif-body` — `word-break: break-word; white-space: pre-wrap` на теле сообщения

## Тестовые аккаунты

Все пароли: `12345678`

| Email | Роль | Описание |
|-------|------|----------|
| admin@admin.com | admin | Полный доступ |
| fk2ato5px1@gmail.com | vice_principal | Завуч |
| ivan@ivan.com | teacher | Учитель (История, класс 1В) |
| igor@igor.com | student | Ученик класса 1В |
| nikita@nikita.com | parent | Родитель Игоря |

Тестовые данные в БД: классы `1В` и `10А` (2026 г.), предметы «Русский», «Математика», «История».

## Docker Compose сервисы

| Сервис | Образ | Порт | Особенность |
|--------|-------|------|-------------|
| `db` | postgres:16 | из .env | данные в volume `postgres_data`, схема из `sql/init.sql` |
| `api` | ./backend | 8000 | `./backend/app` volume-mounted → hot reload без rebuild |
| `frontend` | ./frontend (nginx) | 80 | файлы baked in образ → нужен `--build` при изменениях |

## Правила разработки

### Backend
- Весь код async/await, никаких sync в роутерах
- ORM-only, никаких `text()` без крайней необходимости
- `lazy="selectin"` на всех relationship
- ENUM поля: `SAEnum(..., create_type=False)` — типы уже созданы в БД
- Ошибки — `HTTPException` с русским `detail`
- HTTP коды: 201 создание, 200 чтение/обновление, 204 удаление, 404 не найдено, 403 нет прав, 409 конфликт
- Validation errors: использовать `field_validator` вместо `pattern=` в Field

### Frontend
- Токен только в `sessionStorage`
- Все данные через `api.get/post/patch/delete`
- `showAlert(err.message)` для показа ошибок пользователю
- Никакого хардкода данных
- Компоненты (navbar, sidebar) подгружаются через fetch в `loadXxxComponents()`
