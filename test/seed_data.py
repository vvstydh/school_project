#!/usr/bin/env python3
"""Заполнение системы демо-данными через API (admin).

Скрипт самодостаточен: не зависит от заранее существующих пользователей
(кроме встроенного admin@admin.com). Безопасно перезапускать —
пользователи/предметы/классы создаются идемпотентно по email/имени,
уроки и оценки добавляются заново при каждом запуске (доп. seed-данные).
"""

from datetime import date, timedelta

import requests

BASE = "http://localhost:8000"
PASSWORD = "12345678"


def login(email, passwords):
    for pwd in passwords:
        r = requests.post(f"{BASE}/auth/login", data={"username": email, "password": pwd})
        if r.status_code == 200:
            return r.json()["access_token"]
    raise SystemExit(f"Не удалось войти как {email}: {r.status_code} {r.text}")


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def post(path, token, body, ok=(200, 201, 409)):
    r = requests.post(f"{BASE}{path}", json=body, headers=auth(token))
    if r.status_code not in ok:
        print(f"  ! POST {path} -> {r.status_code}: {r.text}")
    return r


def get(path, token):
    r = requests.get(f"{BASE}{path}", headers=auth(token))
    r.raise_for_status()
    return r.json()


admin_token = login("admin@admin.com", [PASSWORD, "1234"])
print("admin logged in")

# ── Subjects ────────────────────────────────────────────────────────────────
new_subjects = [
    "Математика", "Русский язык", "Литература", "Физика",
    "Химия", "Биология", "История", "Английский язык",
]
subjects = {s["name"]: s["id"] for s in get("/subjects/", admin_token)}
for name in new_subjects:
    if name not in subjects:
        r = post("/subjects/", admin_token, {"name": name})
        if r.status_code == 201:
            subjects[name] = r.json()["id"]
print("subjects:", len(subjects))

# ── Classes ─────────────────────────────────────────────────────────────────
new_classes = [("1А", 2026), ("4Б", 2026), ("5В", 2026), ("7Г", 2026), ("9А", 2026), ("11Б", 2026)]
classes = {c["name"]: c["id"] for c in get("/classes/", admin_token)}
for name, year in new_classes:
    if name not in classes:
        r = post("/classes/", admin_token, {"name": name, "academic_year": year})
        if r.status_code == 201:
            classes[name] = r.json()["id"]
print("classes:", len(classes))

users = {u["email"]: u for u in get("/users/", admin_token)}


def ensure_user(email, role, fn, ln, mn, body_extra=None):
    if email not in users:
        body = {"email": email, "password": PASSWORD, "role": role,
                "first_name": fn, "last_name": ln, "middle_name": mn}
        body.update(body_extra or {})
        r = post("/users/", admin_token, body)
        if r.status_code == 201:
            users[email] = r.json()
    return users[email]["id"]


# ── Vice principal ────────────────────────────────────────────────────────────
ensure_user("oksana@school.com", "vice_principal", "Оксана", "Васильева", "Леонидовна")

# ── Teachers ────────────────────────────────────────────────────────────────
new_teachers = [
    ("elena@school.com",   "Елена",    "Смирнова",   "Викторовна", "Математика"),
    ("olga@school.com",    "Ольга",    "Кузнецова",  "Андреевна",  "Русский язык"),
    ("anna@school.com",    "Анна",     "Белова",     "Сергеевна",  "Литература"),
    ("sergey@school.com",  "Сергей",   "Иванов",     "Петрович",   "Физика"),
    ("dmitry@school.com",  "Дмитрий",  "Козлов",     "Андреевич",  "Химия"),
    ("tatyana@school.com", "Татьяна",  "Воробьёва",  "Олеговна",   "Биология"),
    ("nikolay@school.com", "Николай",  "Романов",    "Дмитриевич", "История"),
    ("maria@school.com",   "Мария",    "Соколова",   "Игоревна",   "Английский язык"),
]
teachers = {}
for email, fn, ln, mn, subj in new_teachers:
    uid = ensure_user(email, "teacher", fn, ln, mn)
    teachers[subj] = uid
    post(f"/users/{uid}/teacher-profile", admin_token, {"subject_id": subjects[subj]})
print("teachers:", len(teachers))

# ── Teacher <-> Class links ───────────────────────────────────────────────────
tc_links = [
    (teachers["Математика"],       classes["1А"]),
    (teachers["Русский язык"],     classes["1А"]),
    (teachers["Литература"],       classes["1А"]),
    (teachers["Математика"],       classes["4Б"]),
    (teachers["История"],          classes["4Б"]),
    (teachers["Биология"],         classes["4Б"]),
    (teachers["Русский язык"],     classes["5В"]),
    (teachers["Физика"],           classes["5В"]),
    (teachers["Английский язык"],  classes["5В"]),
    (teachers["Литература"],       classes["7Г"]),
    (teachers["Химия"],            classes["7Г"]),
    (teachers["История"],          classes["7Г"]),
    (teachers["Физика"],           classes["9А"]),
    (teachers["Английский язык"],  classes["9А"]),
    (teachers["Химия"],            classes["9А"]),
    (teachers["Биология"],         classes["11Б"]),
    (teachers["Математика"],       classes["11Б"]),
    (teachers["Русский язык"],     classes["11Б"]),
]
for teacher_id, class_id in tc_links:
    post(f"/classes/{class_id}/teachers", admin_token, {"teacher_id": teacher_id, "class_id": class_id})
print("teacher-class links:", len(tc_links))

# ── Students ────────────────────────────────────────────────────────────────
new_students = [
    # 1А
    ("kuzmin@school.com",    "Иван",      "Кузьмин",    "Олегович",    "2019-02-14", "1А"),
    ("tihonova@school.com",  "Мария",     "Тихонова",   "Игоревна",    "2019-05-03", "1А"),
    ("belyaev@school.com",   "Артём",     "Беляев",     "Дмитриевич",  "2019-09-21", "1А"),
    ("nikitina@school.com",  "Дарья",     "Никитина",   "Андреевна",   "2019-11-08", "1А"),
    # 4Б
    ("polyakov@school.com",  "Степан",    "Поляков",    "Викторович",  "2016-01-19", "4Б"),
    ("guseva@school.com",    "Алина",     "Гусева",     "Сергеевна",   "2016-04-27", "4Б"),
    ("vinogradov@school.com","Егор",      "Виноградов", "Романович",   "2016-07-12", "4Б"),
    ("soboleva@school.com",  "Вероника",  "Соболева",   "Денисовна",   "2016-10-30", "4Б"),
    # 5В
    ("bogdanov@school.com",  "Тимур",     "Богданов",   "Маратович",   "2015-03-05", "5В"),
    ("makarova@school.com",  "Ксения",    "Макарова",   "Павловна",    "2015-06-18", "5В"),
    ("andreev@school.com",   "Роман",     "Андреев",    "Игоревич",    "2015-08-22", "5В"),
    ("denisova@school.com",  "Алиса",     "Денисова",   "Олеговна",    "2015-12-09", "5В"),
    # 7Г
    ("safonov@school.com",   "Илья",      "Сафонов",    "Андреевич",   "2013-02-27", "7Г"),
    ("krylova@school.com",   "Юлия",      "Крылова",    "Денисовна",   "2013-05-14", "7Г"),
    ("voronin@school.com",   "Глеб",      "Воронин",    "Викторович",  "2013-09-03", "7Г"),
    ("zimina@school.com",    "Виктория",  "Зимина",     "Романовна",   "2013-11-25", "7Г"),
    # 9А
    ("markin@school.com",    "Денис",     "Маркин",     "Олегович",    "2011-01-16", "9А"),
    ("sorokina@school.com",  "Анастасия", "Сорокина",   "Игоревна",    "2011-04-08", "9А"),
    ("gavrilov@school.com",  "Владислав", "Гаврилов",   "Андреевич",   "2011-07-29", "9А"),
    ("kornilova@school.com", "Елизавета", "Корнилова",  "Денисовна",   "2011-10-12", "9А"),
    # 11Б
    ("konovalov@school.com", "Игорь",     "Коновалов",  "Романович",   "2009-03-22", "11Б"),
    ("klimova@school.com",   "Софья",     "Климова",    "Викторовна",  "2009-06-10", "11Б"),
    ("fomin@school.com",     "Александр", "Фомин",      "Денисович",   "2009-09-17", "11Б"),
    ("zhdanova@school.com",  "Полина",    "Жданова",    "Игоревна",    "2009-12-04", "11Б"),
]
students = {}
for email, fn, ln, mn, dob, cls in new_students:
    sid = ensure_user(email, "student", fn, ln, mn)
    students[email] = (sid, cls)
    post(f"/users/{sid}/student-profile", admin_token, {"date_of_birth": dob})
    post(f"/classes/{classes[cls]}/students", admin_token, {
        "class_id": classes[cls], "student_id": sid, "academic_year": 2026,
    })
print("students:", len(students))

# ── Parents ─────────────────────────────────────────────────────────────────
new_parents = [
    ("orlova_p@school.com",    "Татьяна",  "Орлова",    "Николаевна",   ["kuzmin@school.com", "tihonova@school.com"]),
    ("morozov_p@school.com",   "Александр","Морозов",   "Сергеевич",    ["belyaev@school.com", "nikitina@school.com"]),
    ("zaharova_p@school.com",  "Ирина",    "Захарова",  "Викторовна",   ["polyakov@school.com", "guseva@school.com"]),
    ("goncharov_p@school.com", "Владимир", "Гончаров",  "Олегович",     ["vinogradov@school.com", "soboleva@school.com"]),
    ("belyaeva_p@school.com",  "Наталья",  "Беляева",   "Игоревна",     ["bogdanov@school.com", "makarova@school.com", "andreev@school.com"]),
    ("safonov_p@school.com",   "Андрей",   "Сафонов",   "Викторович",   ["denisova@school.com", "safonov@school.com", "krylova@school.com"]),
    ("voronina_p@school.com",  "Марина",   "Воронина",  "Александровна",["voronin@school.com", "zimina@school.com", "markin@school.com"]),
    ("sorokin_p@school.com",   "Павел",    "Сорокин",   "Игоревич",     ["sorokina@school.com", "gavrilov@school.com", "kornilova@school.com"]),
    ("konovalova_p@school.com","Екатерина","Коновалова","Дмитриевна",   ["konovalov@school.com", "klimova@school.com"]),
    ("fomin_p@school.com",     "Денис",    "Фомин",     "Андреевич",    ["fomin@school.com", "zhdanova@school.com"]),
]
for email, fn, ln, mn, children in new_parents:
    parent_id = ensure_user(email, "parent", fn, ln, mn)
    for child_email in children:
        post(f"/users/parents/{parent_id}/children/{students[child_email][0]}", admin_token, None)
print("parents:", len(new_parents))

# ── Lessons ─────────────────────────────────────────────────────────────────
TODAY = date.today()
TOPICS = {
    "Математика":      "Решение линейных уравнений",
    "Русский язык":    "Правописание безударных гласных в корне",
    "Литература":      "Анализ художественного текста",
    "Физика":          "Законы движения Ньютона",
    "Химия":           "Периодическая система элементов",
    "Биология":        "Строение клетки",
    "История":         "Эпоха великих реформ",
    "Английский язык": "Время Past Simple: образование и употребление",
}
subj_by_teacher = {tid: subj for subj, tid in teachers.items()}

lessons = []
for idx, (teacher_id, class_id) in enumerate(tc_links):
    subj = subj_by_teacher[teacher_id]
    lesson_date = (TODAY + timedelta(days=1 + idx)).isoformat()
    r = post("/lessons/", admin_token, {
        "class_id": class_id, "teacher_id": teacher_id, "subject_id": subjects[subj],
        "date": lesson_date, "topic": TOPICS[subj],
    })
    if r.status_code == 201:
        lessons.append(r.json())
print("lessons created:", len(lessons))

# class_id -> [student_id]
class_students = {}
for email, (sid, cls) in students.items():
    class_students.setdefault(classes[cls], []).append(sid)

# ── Grades + Attendances ──────────────────────────────────────────────────────
grade_cycle = [5, 4, 3, 5, 4, 2]
att_cycle = ["present", "present", "late", "present", "absent", "excused"]
i = 0
for lesson in lessons:
    for sid in class_students.get(lesson["class_id"], []):
        post("/grades/", admin_token, {
            "lesson_id": lesson["id"], "student_id": sid,
            "value": grade_cycle[i % len(grade_cycle)],
        })
        post("/attendances/", admin_token, {
            "lesson_id": lesson["id"], "student_id": sid,
            "status": att_cycle[i % len(att_cycle)],
        })
        i += 1
print("grades/attendances created:", i)

# ── Notifications ──────────────────────────────────────────────────────────────
student_ids = [students[e][0] for e in students]
teacher_ids = list(teachers.values())

for sid in student_ids:
    post("/notifications/", admin_token, {
        "recipient_id": sid,
        "title": "Добро пожаловать в Зурнал",
        "body": "Ваш аккаунт активирован. Следите за расписанием уроков и оценками в системе.",
    })

for tid in teacher_ids:
    post("/notifications/", admin_token, {
        "recipient_id": tid,
        "title": "Обновление расписания",
        "body": "Проверьте актуальное расписание уроков на следующую неделю в личном кабинете.",
    })

print("notifications created:", len(student_ids) + len(teacher_ids))
print("done")
