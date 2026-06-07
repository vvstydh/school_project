# Схема базы данных — Электронный школьный журнал

## ENUM типы

| Тип | Значения |
|-----|----------|
| `user_role` | `admin`, `vice_principal`, `teacher`, `student`, `parent` |
| `attendance_status` | `present`, `absent`, `late`, `excused` |

---

## Таблицы

### `users`

| Поле | Тип | Ключ | NULL | Ограничение |
|------|-----|------|------|-------------|
| `id` | `UUID` | PK | NOT NULL | `DEFAULT gen_random_uuid()` |
| `email` | `VARCHAR(255)` | UQ | NOT NULL | Формат email, длина 5–255 |
| `password_hash` | `TEXT` | — | NOT NULL | `LENGTH >= 60` |
| `role` | `user_role` | — | NOT NULL | ENUM |
| `first_name` | `VARCHAR(100)` | — | NOT NULL | `^[А-ЯЁ][а-яё\-]+$`, длина 2–100 |
| `last_name` | `VARCHAR(100)` | — | NOT NULL | `^[А-ЯЁ][а-яё\-]+$`, длина 2–100 |
| `middle_name` | `VARCHAR(100)` | — | NULL | `^[А-ЯЁ][а-яё]+$`, длина 2–100 |
| `is_active` | `BOOLEAN` | — | NOT NULL | `DEFAULT TRUE` |
| `created_at` | `TIMESTAMPTZ` | — | NOT NULL | `DEFAULT now()` |
| `updated_at` | `TIMESTAMPTZ` | — | NOT NULL | `DEFAULT now()`, обновляется триггером |

**Индексы:** `email`, `role`, `is_active` (частичный: только `TRUE`)

---

### `subjects`

| Поле | Тип | Ключ | NULL | Ограничение |
|------|-----|------|------|-------------|
| `id` | `UUID` | PK | NOT NULL | `DEFAULT gen_random_uuid()` |
| `name` | `VARCHAR(100)` | UQ | NOT NULL | `^[А-ЯЁа-яё][А-ЯЁа-яё\s\-]+$`, длина 2–100 |
| `created_at` | `TIMESTAMPTZ` | — | NOT NULL | `DEFAULT now()` |
| `updated_at` | `TIMESTAMPTZ` | — | NOT NULL | `DEFAULT now()`, обновляется триггером |

---

### `classes`

| Поле | Тип | Ключ | NULL | Ограничение |
|------|-----|------|------|-------------|
| `id` | `UUID` | PK | NOT NULL | `DEFAULT gen_random_uuid()` |
| `name` | `VARCHAR(10)` | UQ совместно с `academic_year` | NOT NULL | `^[1-9][0-9]?[А-ЯЁ]$` (например `1В`, `10А`) |
| `academic_year` | `SMALLINT` | UQ совместно с `name` | NOT NULL | 2000–2100 |
| `created_at` | `TIMESTAMPTZ` | — | NOT NULL | `DEFAULT now()` |
| `updated_at` | `TIMESTAMPTZ` | — | NOT NULL | `DEFAULT now()`, обновляется триггером |

**Индексы:** нет дополнительных

**Связи:** нет внешних ключей (связи только через `class_students` и `teacher_classes`)

---

### `teacher_profiles`

| Поле | Тип | Ключ | NULL | Ограничение |
|------|-----|------|------|-------------|
| `id` | `UUID` | PK | NOT NULL | `DEFAULT gen_random_uuid()` |
| `user_id` | `UUID` | UQ, FK → `users.id` | NOT NULL | `ON DELETE CASCADE` |
| `subject_id` | `UUID` | FK → `subjects.id` | NOT NULL | `ON DELETE RESTRICT` |
| `created_at` | `TIMESTAMPTZ` | — | NOT NULL | `DEFAULT now()` |
| `updated_at` | `TIMESTAMPTZ` | — | NOT NULL | `DEFAULT now()`, обновляется триггером |

**Индексы:** `subject_id`

**Связи:**
- `user_id` → `users.id` (1:1, ON DELETE CASCADE)
- `subject_id` → `subjects.id` (ON DELETE RESTRICT — нельзя удалить предмет с учителем)

---

### `student_profiles`

| Поле | Тип | Ключ | NULL | Ограничение |
|------|-----|------|------|-------------|
| `id` | `UUID` | PK | NOT NULL | `DEFAULT gen_random_uuid()` |
| `user_id` | `UUID` | UQ, FK → `users.id` | NOT NULL | `ON DELETE CASCADE` |
| `date_of_birth` | `DATE` | — | NULL | 1990-01-01 .. (сегодня − 5 лет) |
| `created_at` | `TIMESTAMPTZ` | — | NOT NULL | `DEFAULT now()` |
| `updated_at` | `TIMESTAMPTZ` | — | NOT NULL | `DEFAULT now()`, обновляется триггером |

**Связи:**
- `user_id` → `users.id` (1:1, ON DELETE CASCADE)

---

### `parent_student`

| Поле | Тип | Ключ | NULL | Ограничение |
|------|-----|------|------|-------------|
| `parent_id` | `UUID` | PK (совместный), FK → `users.id` | NOT NULL | `ON DELETE CASCADE` |
| `student_id` | `UUID` | PK (совместный), FK → `users.id` | NOT NULL | `ON DELETE CASCADE` |

**Ограничения:** `parent_id <> student_id`

**Индексы:** `parent_id`, `student_id`

**Связи:**
- `parent_id` → `users.id` (родитель, ON DELETE CASCADE)
- `student_id` → `users.id` (ученик, ON DELETE CASCADE)

*M:M между пользователями с ролью `parent` и `student`*

---

### `class_students`

| Поле | Тип | Ключ | NULL | Ограничение |
|------|-----|------|------|-------------|
| `id` | `UUID` | PK | NOT NULL | `DEFAULT gen_random_uuid()` |
| `class_id` | `UUID` | FK → `classes.id` | NOT NULL | `ON DELETE CASCADE` |
| `student_id` | `UUID` | UQ совместно с `academic_year`, FK → `users.id` | NOT NULL | `ON DELETE CASCADE` |
| `academic_year` | `SMALLINT` | UQ совместно с `student_id` | NOT NULL | 2000–2100 |
| `enrolled_at` | `DATE` | — | NOT NULL | `DEFAULT CURRENT_DATE`, `<= CURRENT_DATE` |

**Индексы:** `class_id`, `student_id`

**Связи:**
- `class_id` → `classes.id` (ON DELETE CASCADE)
- `student_id` → `users.id` (ON DELETE CASCADE)

*Один ученик — один класс в году (UNIQUE student_id + academic_year)*

---

### `teacher_classes`

| Поле | Тип | Ключ | NULL | Ограничение |
|------|-----|------|------|-------------|
| `id` | `UUID` | PK | NOT NULL | `DEFAULT gen_random_uuid()` |
| `teacher_id` | `UUID` | UQ совместно с `class_id`, FK → `users.id` | NOT NULL | `ON DELETE CASCADE` |
| `class_id` | `UUID` | UQ совместно с `teacher_id`, FK → `classes.id` | NOT NULL | `ON DELETE CASCADE` |
| `created_at` | `TIMESTAMPTZ` | — | NOT NULL | `DEFAULT now()` |

**Индексы:** `teacher_id`, `class_id`

**Связи:**
- `teacher_id` → `users.id` (ON DELETE CASCADE)
- `class_id` → `classes.id` (ON DELETE CASCADE)

*M:M учитель ↔ класс (один учитель ведёт в нескольких классах)*

---

### `lessons`

| Поле | Тип | Ключ | NULL | Ограничение |
|------|-----|------|------|-------------|
| `id` | `UUID` | PK | NOT NULL | `DEFAULT gen_random_uuid()` |
| `class_id` | `UUID` | FK → `classes.id` | NOT NULL | `ON DELETE CASCADE` |
| `teacher_id` | `UUID` | FK → `users.id` | NOT NULL | `ON DELETE RESTRICT` |
| `subject_id` | `UUID` | FK → `subjects.id` | NOT NULL | `ON DELETE RESTRICT` |
| `date` | `DATE` | — | NOT NULL | 2000-01-01 .. (сегодня + 1 год) |
| `topic` | `VARCHAR(500)` | — | NULL | `^[А-ЯЁа-яё].*`, длина 2–500, не пустая строка |
| `created_at` | `TIMESTAMPTZ` | — | NOT NULL | `DEFAULT now()` |
| `updated_at` | `TIMESTAMPTZ` | — | NOT NULL | `DEFAULT now()`, обновляется триггером |

**Индексы:** `(class_id, date)`, `teacher_id`, `subject_id`, `date`

**Связи:**
- `class_id` → `classes.id` (ON DELETE CASCADE)
- `teacher_id` → `users.id` (ON DELETE RESTRICT — нельзя удалить учителя с уроками)
- `subject_id` → `subjects.id` (ON DELETE RESTRICT — нельзя удалить предмет с уроками)

---

### `grades`

| Поле | Тип | Ключ | NULL | Ограничение |
|------|-----|------|------|-------------|
| `id` | `UUID` | PK | NOT NULL | `DEFAULT gen_random_uuid()` |
| `lesson_id` | `UUID` | UQ совместно с `student_id`, FK → `lessons.id` | NOT NULL | `ON DELETE CASCADE` |
| `student_id` | `UUID` | UQ совместно с `lesson_id`, FK → `users.id` | NOT NULL | `ON DELETE CASCADE` |
| `value` | `SMALLINT` | — | NOT NULL | 1–5 |
| `comment` | `TEXT` | — | NULL | длина 2–1000, не пустая строка |
| `created_at` | `TIMESTAMPTZ` | — | NOT NULL | `DEFAULT now()` |
| `updated_at` | `TIMESTAMPTZ` | — | NOT NULL | `DEFAULT now()`, обновляется триггером |

**Индексы:** `student_id`, `lesson_id`

**Связи:**
- `lesson_id` → `lessons.id` (ON DELETE CASCADE)
- `student_id` → `users.id` (ON DELETE CASCADE)

*Одна оценка на пару (ученик, урок)*

---

### `attendances`

| Поле | Тип | Ключ | NULL | Ограничение |
|------|-----|------|------|-------------|
| `id` | `UUID` | PK | NOT NULL | `DEFAULT gen_random_uuid()` |
| `lesson_id` | `UUID` | UQ совместно с `student_id`, FK → `lessons.id` | NOT NULL | `ON DELETE CASCADE` |
| `student_id` | `UUID` | UQ совместно с `lesson_id`, FK → `users.id` | NOT NULL | `ON DELETE CASCADE` |
| `status` | `attendance_status` | — | NOT NULL | ENUM, `DEFAULT 'present'` |
| `created_at` | `TIMESTAMPTZ` | — | NOT NULL | `DEFAULT now()` |
| `updated_at` | `TIMESTAMPTZ` | — | NOT NULL | `DEFAULT now()`, обновляется триггером |

**Индексы:** `student_id`, `lesson_id`

**Связи:**
- `lesson_id` → `lessons.id` (ON DELETE CASCADE)
- `student_id` → `users.id` (ON DELETE CASCADE)

*Одна запись посещаемости на пару (ученик, урок)*

---

### `notifications`

| Поле | Тип | Ключ | NULL | Ограничение |
|------|-----|------|------|-------------|
| `id` | `UUID` | PK | NOT NULL | `DEFAULT gen_random_uuid()` |
| `recipient_id` | `UUID` | FK → `users.id` | NOT NULL | `ON DELETE CASCADE` |
| `title` | `VARCHAR(255)` | — | NOT NULL | длина 2–255, не пустая строка |
| `body` | `TEXT` | — | NOT NULL | длина 2–5000, не пустая строка |
| `is_read` | `BOOLEAN` | — | NOT NULL | `DEFAULT FALSE` |
| `created_at` | `TIMESTAMPTZ` | — | NOT NULL | `DEFAULT now()` |

**Индексы:** `(recipient_id, is_read)` (частичный: только `is_read = FALSE`)

**Связи:**
- `recipient_id` → `users.id` (ON DELETE CASCADE)

*Нет `updated_at` — уведомления не редактируются*

---

## Схема связей между таблицами

```
users ──────────────────────────────────────────────────┐
  │  1:1 → teacher_profiles (user_id)                   │
  │  1:1 → student_profiles (user_id)                   │
  │  M:M → users (parent_student: parent_id/student_id) │
  │  M:M → classes (teacher_classes: teacher_id)        │
  │  M:M → classes (class_students: student_id)         │
  │  1:N → lessons (teacher_id)                         │
  │  1:N → grades (student_id)                          │
  │  1:N → attendances (student_id)                     │
  └──── 1:N → notifications (recipient_id)              │
                                                         │
subjects ──────────────────────────────────────────────┐ │
  │  1:1 → teacher_profiles (subject_id)               │ │
  └──── 1:N → lessons (subject_id)                     │ │
                                                        │ │
classes ────────────────────────────────────────────┐  │ │
  │  M:M → users (class_students: class_id)         │  │ │
  │  M:M → users (teacher_classes: class_id)        │  │ │
  └──── 1:N → lessons (class_id)                    │  │ │
                                                     │  │ │
lessons ─────────────────────────────────────────┐  │  │ │
  │  1:N → grades (lesson_id)                    │  │  │ │
  └──── 1:N → attendances (lesson_id)            │  │  │ │
                                                  │  │  │ │
grades ◄──────────────────────────────────────────┘  │  │ │
attendances ◄────────────────────────────────────────┘  │ │
teacher_profiles ◄───────────────────────────────────────┘ │
student_profiles, class_students, teacher_classes,          │
notifications, parent_student ◄─────────────────────────────┘
```

## Триггер auto `updated_at`

Функция `fn_set_updated_at()` автоматически устанавливает `updated_at = now()` при каждом `UPDATE` для таблиц:
`users`, `subjects`, `classes`, `teacher_profiles`, `student_profiles`, `lessons`, `grades`, `attendances`

*Таблица `notifications` не имеет `updated_at` — уведомления не изменяются после создания.*
