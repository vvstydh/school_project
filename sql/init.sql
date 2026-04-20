-- ============================================================
-- ЭЛЕКТРОННЫЙ ШКОЛЬНЫЙ ЖУРНАЛ
-- Полный скрипт миграции БД
-- Запускать в pgAdmin: Query Tool → вставить → F5
-- ============================================================


-- ============================================================
-- БЛОК 1: ТИПЫ (ENUM)
-- ============================================================

CREATE TYPE user_role AS ENUM (
    'admin',
    'vice_principal',
    'teacher',
    'student',
    'parent'
);

CREATE TYPE attendance_status AS ENUM (
    'present',
    'absent',
    'late',
    'excused'
);


-- ============================================================
-- БЛОК 2: ТАБЛИЦА ПОЛЬЗОВАТЕЛЕЙ
-- ============================================================

CREATE TABLE users (
    id            UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    email         VARCHAR(255)  NOT NULL,
    password_hash TEXT          NOT NULL,
    role          user_role     NOT NULL,
    first_name    VARCHAR(100)  NOT NULL,
    last_name     VARCHAR(100)  NOT NULL,
    middle_name   VARCHAR(100)  NULL,
    is_active     BOOLEAN       NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ   NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ   NOT NULL DEFAULT now(),

    CONSTRAINT uq_users_email
        UNIQUE (email),

    CONSTRAINT chk_users_email
        CHECK (email ~* '^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$'),

    CONSTRAINT chk_users_email_length
        CHECK (LENGTH(email) BETWEEN 5 AND 255),

    CONSTRAINT chk_users_password_hash_length
        CHECK (LENGTH(password_hash) >= 60),

    CONSTRAINT chk_users_first_name
        CHECK (
            LENGTH(first_name) BETWEEN 2 AND 100
            AND first_name ~ '^[А-ЯЁ][а-яё\-]+$'
        ),

    CONSTRAINT chk_users_last_name
        CHECK (
            LENGTH(last_name) BETWEEN 2 AND 100
            AND last_name ~ '^[А-ЯЁ][а-яё\-]+$'
        ),

    CONSTRAINT chk_users_middle_name
        CHECK (
            middle_name IS NULL
            OR (
                LENGTH(middle_name) BETWEEN 2 AND 100
                AND middle_name ~ '^[А-ЯЁ][а-яё]+$'
            )
        )
);

CREATE INDEX idx_users_email  ON users (email);
CREATE INDEX idx_users_role   ON users (role);
CREATE INDEX idx_users_active ON users (is_active) WHERE is_active = TRUE;


-- ============================================================
-- БЛОК 3: СПРАВОЧНИК ПРЕДМЕТОВ
-- ============================================================

CREATE TABLE subjects (
    id         UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    name       VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ  NOT NULL DEFAULT now(),

    CONSTRAINT uq_subjects_name
        UNIQUE (name),

    CONSTRAINT chk_subjects_name
        CHECK (
            LENGTH(name) BETWEEN 2 AND 100
            AND name ~ '^[А-ЯЁа-яё][А-ЯЁа-яё\s\-]+$'
        )
);


-- ============================================================
-- БЛОК 4: КЛАССЫ
-- ============================================================

CREATE TABLE classes (
    id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name              VARCHAR(10) NOT NULL,
    academic_year     SMALLINT    NOT NULL,
    vice_principal_id UUID        NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_classes_name_year
        UNIQUE (name, academic_year),

    CONSTRAINT chk_classes_name
        CHECK (name ~ '^[1-9][0-9]?[А-ЯЁ]$'),

    CONSTRAINT chk_classes_academic_year
        CHECK (academic_year BETWEEN 2000 AND 2100),

    CONSTRAINT fk_classes_vice_principal
        FOREIGN KEY (vice_principal_id)
        REFERENCES users (id)
        ON DELETE SET NULL
);

CREATE INDEX idx_classes_vice_principal ON classes (vice_principal_id)
    WHERE vice_principal_id IS NOT NULL;


-- ============================================================
-- БЛОК 5: ПРОФИЛИ УЧИТЕЛЕЙ И УЧЕНИКОВ
-- ============================================================

CREATE TABLE teacher_profiles (
    id         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID        NOT NULL,
    subject_id UUID        NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_teacher_profiles_user
        UNIQUE (user_id),

    CONSTRAINT fk_teacher_profiles_user
        FOREIGN KEY (user_id)
        REFERENCES users (id)
        ON DELETE CASCADE,

    CONSTRAINT fk_teacher_profiles_subject
        FOREIGN KEY (subject_id)
        REFERENCES subjects (id)
        ON DELETE RESTRICT
);

CREATE INDEX idx_teacher_profiles_subject ON teacher_profiles (subject_id);

-- ----

CREATE TABLE student_profiles (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID        NOT NULL,
    date_of_birth DATE        NULL,
    record_number VARCHAR(50) NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_student_profiles_user
        UNIQUE (user_id),

    CONSTRAINT uq_student_profiles_record
        UNIQUE (record_number),

    CONSTRAINT fk_student_profiles_user
        FOREIGN KEY (user_id)
        REFERENCES users (id)
        ON DELETE CASCADE,

    CONSTRAINT chk_student_profiles_dob
        CHECK (
            date_of_birth IS NULL
            OR (
                date_of_birth BETWEEN '1990-01-01'
                AND (CURRENT_DATE - INTERVAL '5 years')::DATE
            )
        ),

    CONSTRAINT chk_student_profiles_record
        CHECK (
            record_number IS NULL
            OR (
                LENGTH(record_number) BETWEEN 1 AND 50
                AND record_number ~ '^[А-ЯЁа-яёA-Za-z0-9\-\/]+$'
            )
        )
);


-- ============================================================
-- БЛОК 6: СВЯЗУЮЩИЕ ТАБЛИЦЫ
-- ============================================================

CREATE TABLE class_students (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    class_id      UUID        NOT NULL,
    student_id    UUID        NOT NULL,
    academic_year SMALLINT    NOT NULL,
    enrolled_at   DATE        NOT NULL DEFAULT CURRENT_DATE,

    CONSTRAINT uq_class_students_student_year
        UNIQUE (student_id, academic_year),

    CONSTRAINT fk_class_students_class
        FOREIGN KEY (class_id)
        REFERENCES classes (id)
        ON DELETE CASCADE,

    CONSTRAINT fk_class_students_student
        FOREIGN KEY (student_id)
        REFERENCES users (id)
        ON DELETE CASCADE,

    CONSTRAINT chk_class_students_year
        CHECK (academic_year BETWEEN 2000 AND 2100),

    CONSTRAINT chk_class_students_enrolled_at
        CHECK (enrolled_at <= CURRENT_DATE)
);

CREATE INDEX idx_class_students_class   ON class_students (class_id);
CREATE INDEX idx_class_students_student ON class_students (student_id);

-- ----

CREATE TABLE teacher_classes (
    id         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id UUID        NOT NULL,
    class_id   UUID        NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_teacher_classes
        UNIQUE (teacher_id, class_id),

    CONSTRAINT fk_teacher_classes_teacher
        FOREIGN KEY (teacher_id)
        REFERENCES users (id)
        ON DELETE CASCADE,

    CONSTRAINT fk_teacher_classes_class
        FOREIGN KEY (class_id)
        REFERENCES classes (id)
        ON DELETE CASCADE
);

CREATE INDEX idx_teacher_classes_teacher ON teacher_classes (teacher_id);
CREATE INDEX idx_teacher_classes_class   ON teacher_classes (class_id);

-- ----

CREATE TABLE parent_student (
    parent_id  UUID NOT NULL,
    student_id UUID NOT NULL,

    CONSTRAINT pk_parent_student
        PRIMARY KEY (parent_id, student_id),

    CONSTRAINT fk_parent_student_parent
        FOREIGN KEY (parent_id)
        REFERENCES users (id)
        ON DELETE CASCADE,

    CONSTRAINT fk_parent_student_student
        FOREIGN KEY (student_id)
        REFERENCES users (id)
        ON DELETE CASCADE,

    CONSTRAINT chk_parent_student_not_self
        CHECK (parent_id <> student_id)
);

CREATE INDEX idx_parent_student_parent  ON parent_student (parent_id);
CREATE INDEX idx_parent_student_student ON parent_student (student_id);


-- ============================================================
-- БЛОК 7: УРОКИ
-- ============================================================

CREATE TABLE lessons (
    id         UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    class_id   UUID         NOT NULL,
    teacher_id UUID         NOT NULL,
    subject_id UUID         NOT NULL,
    date       DATE         NOT NULL,
    topic      VARCHAR(500) NULL,
    created_at TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ  NOT NULL DEFAULT now(),

    CONSTRAINT fk_lessons_class
        FOREIGN KEY (class_id)
        REFERENCES classes (id)
        ON DELETE CASCADE,

    CONSTRAINT fk_lessons_teacher
        FOREIGN KEY (teacher_id)
        REFERENCES users (id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_lessons_subject
        FOREIGN KEY (subject_id)
        REFERENCES subjects (id)
        ON DELETE RESTRICT,

    CONSTRAINT chk_lessons_date
        CHECK (
            date >= '2000-01-01'
            AND date <= (CURRENT_DATE + INTERVAL '1 year')::DATE
        ),

    CONSTRAINT chk_lessons_topic
        CHECK (
            topic IS NULL
            OR (
                LENGTH(topic) BETWEEN 2 AND 500
                AND topic ~ '^[А-ЯЁа-яё].*'
                AND topic !~ '^\s+$'
            )
        )
);

CREATE INDEX idx_lessons_class_date ON lessons (class_id, date);
CREATE INDEX idx_lessons_teacher    ON lessons (teacher_id);
CREATE INDEX idx_lessons_subject    ON lessons (subject_id);
CREATE INDEX idx_lessons_date       ON lessons (date);


-- ============================================================
-- БЛОК 8: ОЦЕНКИ
-- ============================================================

CREATE TABLE grades (
    id         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    lesson_id  UUID        NOT NULL,
    student_id UUID        NOT NULL,
    value      SMALLINT    NOT NULL,
    comment    TEXT        NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_grades_lesson_student
        UNIQUE (lesson_id, student_id),

    CONSTRAINT fk_grades_lesson
        FOREIGN KEY (lesson_id)
        REFERENCES lessons (id)
        ON DELETE CASCADE,

    CONSTRAINT fk_grades_student
        FOREIGN KEY (student_id)
        REFERENCES users (id)
        ON DELETE CASCADE,

    CONSTRAINT chk_grades_value
        CHECK (value BETWEEN 1 AND 5),

    CONSTRAINT chk_grades_comment
        CHECK (
            comment IS NULL
            OR (
                LENGTH(comment) BETWEEN 2 AND 1000
                AND comment !~ '^\s+$'
            )
        )
);

CREATE INDEX idx_grades_student ON grades (student_id);
CREATE INDEX idx_grades_lesson  ON grades (lesson_id);


-- ============================================================
-- БЛОК 9: ПОСЕЩАЕМОСТЬ
-- ============================================================

CREATE TABLE attendances (
    id         UUID              PRIMARY KEY DEFAULT gen_random_uuid(),
    lesson_id  UUID              NOT NULL,
    student_id UUID              NOT NULL,
    status     attendance_status NOT NULL DEFAULT 'present',
    created_at TIMESTAMPTZ       NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ       NOT NULL DEFAULT now(),

    CONSTRAINT uq_attendances_lesson_student
        UNIQUE (lesson_id, student_id),

    CONSTRAINT fk_attendances_lesson
        FOREIGN KEY (lesson_id)
        REFERENCES lessons (id)
        ON DELETE CASCADE,

    CONSTRAINT fk_attendances_student
        FOREIGN KEY (student_id)
        REFERENCES users (id)
        ON DELETE CASCADE
);

CREATE INDEX idx_attendances_student ON attendances (student_id);
CREATE INDEX idx_attendances_lesson  ON attendances (lesson_id);


-- ============================================================
-- БЛОК 10: УВЕДОМЛЕНИЯ
-- ============================================================

CREATE TABLE notifications (
    id           UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    recipient_id UUID         NOT NULL,
    title        VARCHAR(255) NOT NULL,
    body         TEXT         NOT NULL,
    is_read      BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT now(),

    CONSTRAINT fk_notifications_recipient
        FOREIGN KEY (recipient_id)
        REFERENCES users (id)
        ON DELETE CASCADE,

    CONSTRAINT chk_notifications_title
        CHECK (
            LENGTH(title) BETWEEN 2 AND 255
            AND title !~ '^\s+$'
        ),

    CONSTRAINT chk_notifications_body
        CHECK (
            LENGTH(body) BETWEEN 2 AND 5000
            AND body !~ '^\s+$'
        )
);

CREATE INDEX idx_notifications_recipient_unread
    ON notifications (recipient_id, is_read)
    WHERE is_read = FALSE;


-- ============================================================
-- БЛОК 11: ТРИГГЕР auto updated_at
-- ============================================================

CREATE OR REPLACE FUNCTION fn_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
DECLARE
    tbl TEXT;
BEGIN
    FOREACH tbl IN ARRAY ARRAY[
        'users',
        'subjects',
        'classes',
        'teacher_profiles',
        'student_profiles',
        'lessons',
        'grades',
        'attendances'
    ]
    LOOP
        EXECUTE format('
            CREATE TRIGGER trg_%I_updated_at
            BEFORE UPDATE ON %I
            FOR EACH ROW
            EXECUTE FUNCTION fn_set_updated_at()
        ', tbl, tbl);
    END LOOP;
END;
$$;
