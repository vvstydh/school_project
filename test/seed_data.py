#!/usr/bin/env python3
"""Заполнение системы демо-данными через API (admin)."""

from datetime import date, timedelta

import requests

BASE = "http://localhost:8000"
PASSWORD = "12345678"


def login(email, password):
    r = requests.post(f"{BASE}/auth/login", data={"username": email, "password": password})
    r.raise_for_status()
    return r.json()["access_token"]


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


admin_token = login("admin@admin.com", PASSWORD)
print("admin logged in")

# ── Subjects ────────────────────────────────────────────────────────────────
new_subjects = ["Математика", "Русский язык", "Физика", "Английский язык"]
subjects = {s["name"]: s["id"] for s in get("/subjects/", admin_token)}
for name in new_subjects:
    if name not in subjects:
        r = post("/subjects/", admin_token, {"name": name})
        if r.status_code == 201:
            subjects[name] = r.json()["id"]
print("subjects:", subjects)

# ── Classes ─────────────────────────────────────────────────────────────────
new_classes = [("5Б", 2026), ("7Г", 2026), ("9А", 2026)]
classes = {c["name"]: c["id"] for c in get("/classes/", admin_token)}
for name, year in new_classes:
    if name not in classes:
        r = post("/classes/", admin_token, {"name": name, "academic_year": year})
        if r.status_code == 201:
            classes[name] = r.json()["id"]
print("classes:", classes)

# ── Teachers ────────────────────────────────────────────────────────────────
new_teachers = [
    ("elena@school.com",  "Елена",   "Смирнова",  "Викторовна", "Математика"),
    ("olga@school.com",   "Ольга",   "Кузнецова", "Андреевна",  "Русский язык"),
    ("sergey@school.com", "Сергей",  "Иванов",    "Петрович",   "Физика"),
    ("maria@school.com",  "Мария",   "Соколова",  "Игоревна",   "Английский язык"),
]
users = {u["email"]: u for u in get("/users/", admin_token)}

# ── Vice principal ────────────────────────────────────────────────────────────
new_vp = [("oksana@school.com", "Оксана", "Васильева", "Леонидовна")]
for email, fn, ln, mn in new_vp:
    if email not in users:
        r = post("/users/", admin_token, {
            "email": email, "password": PASSWORD, "role": "vice_principal",
            "first_name": fn, "last_name": ln, "middle_name": mn,
        })
        if r.status_code == 201:
            users[email] = r.json()

teachers = {}
for email, fn, ln, mn, subj in new_teachers:
    if email not in users:
        r = post("/users/", admin_token, {
            "email": email, "password": PASSWORD, "role": "teacher",
            "first_name": fn, "last_name": ln, "middle_name": mn,
        })
        if r.status_code == 201:
            users[email] = r.json()
    teachers[subj] = users[email]["id"]
    post(f"/users/{users[email]['id']}/teacher-profile", admin_token, {"subject_id": subjects[subj]})

# existing teacher Данила -> История
danila = users.get("danil@danil.com")
if danila:
    teachers["История"] = danila["id"]
    post(f"/users/{danila['id']}/teacher-profile", admin_token, {"subject_id": subjects.get("История") or list(subjects.values())[0]})
    history_subj = next((s for s in get("/subjects/", admin_token) if s["name"] == "История"), None)
    if history_subj:
        subjects["История"] = history_subj["id"]
        post(f"/users/{danila['id']}/teacher-profile", admin_token, {"subject_id": history_subj["id"]})

print("teachers:", teachers)

# ── Teacher <-> Class links ───────────────────────────────────────────────────
tc_links = [
    (teachers["История"],          classes["10А"]),
    (teachers["История"],          classes["5Б"]),
    (teachers["Математика"],       classes["5Б"]),
    (teachers["Математика"],       classes["7Г"]),
    (teachers["Математика"],       classes["1В"]),
    (teachers["Русский язык"],     classes["7Г"]),
    (teachers["Русский язык"],     classes["9А"]),
    (teachers["Физика"],           classes["9А"]),
    (teachers["Английский язык"],  classes["1В"]),
    (teachers["Английский язык"],  classes["10А"]),
]
for teacher_id, class_id in tc_links:
    post(f"/classes/{class_id}/teachers", admin_token, {"teacher_id": teacher_id, "class_id": class_id})

# ── Students ────────────────────────────────────────────────────────────────
new_students = [
    ("orlov@school.com",    "Дмитрий",   "Орлов",     "Сергеевич",  "2015-03-12", "5Б"),
    ("volkova@school.com",  "Анна",      "Волкова",   "Игоревна",   "2015-07-22", "5Б"),
    ("solovyov@school.com", "Кирилл",    "Соловьёв",  "Андреевич",  "2015-01-30", "5Б"),
    ("morozova@school.com", "Екатерина", "Морозова",  "Павловна",   "2013-05-10", "7Г"),
    ("novikov@school.com",  "Артём",     "Новиков",   "Денисович",  "2013-09-15", "7Г"),
    ("zaharova@school.com", "Полина",    "Захарова",  "Романовна",  "2013-11-30", "7Г"),
    ("fedorov@school.com",  "Максим",    "Фёдоров",   "Олегович",   "2011-02-18", "9А"),
    ("pavlova@school.com",  "Виктория",  "Павлова",   "Дмитриевна", "2011-06-25", "9А"),
    ("goncharov@school.com","Никита",    "Гончаров",  "Максимович", "2011-12-01", "9А"),
    ("zhukova@school.com",  "Софья",     "Жукова",    "Антоновна",  "2018-04-10", "1В"),
    ("sidorov@school.com",  "Михаил",    "Сидоров",   "Викторович", "2018-08-19", "1В"),
]
students = {}
for email, fn, ln, mn, dob, cls in new_students:
    if email not in users:
        r = post("/users/", admin_token, {
            "email": email, "password": PASSWORD, "role": "student",
            "first_name": fn, "last_name": ln, "middle_name": mn,
        })
        if r.status_code == 201:
            users[email] = r.json()
    sid = users[email]["id"]
    students[email] = (sid, cls)
    post(f"/users/{sid}/student-profile", admin_token, {"date_of_birth": dob})
    post(f"/classes/{classes[cls]}/students", admin_token, {
        "class_id": classes[cls], "student_id": sid, "academic_year": 2026,
    })

print("students:", len(students))

# ── Parents ─────────────────────────────────────────────────────────────────
new_parents = [
    ("orlova_p@school.com",   "Татьяна",    "Орлова",    "Николаевна", ["orlov@school.com", "volkova@school.com"]),
    ("morozov_p@school.com",  "Александр",  "Морозов",   "Сергеевич",  ["morozova@school.com", "novikov@school.com"]),
    ("zaharova_p@school.com", "Ирина",      "Захарова",  "Викторовна", ["zaharova@school.com", "fedorov@school.com"]),
    ("goncharov_p@school.com","Владимир",   "Гончаров",  "Олегович",   ["goncharov@school.com", "pavlova@school.com", "zhukova@school.com", "sidorov@school.com"]),
]
for email, fn, ln, mn, children in new_parents:
    if email not in users:
        r = post("/users/", admin_token, {
            "email": email, "password": PASSWORD, "role": "parent",
            "first_name": fn, "last_name": ln, "middle_name": mn,
        })
        if r.status_code == 201:
            users[email] = r.json()
    parent_id = users[email]["id"]
    for child_email in children:
        post(f"/users/parents/{parent_id}/children/{students[child_email][0]}", admin_token, {})

# link existing parent ded@ded.com -> anton@anton.com
parent_ded = users.get("ded@ded.com")
student_anton = users.get("anton@anton.com")
if parent_ded and student_anton:
    post(f"/users/parents/{parent_ded['id']}/children/{student_anton['id']}", admin_token, {})

print("parents linked")

# ── Lessons ─────────────────────────────────────────────────────────────────
TODAY = date.today()
lesson_defs = [
    (classes["10А"], teachers["Английский язык"], subjects["Английский язык"], 4,  "Время Present Perfect: образование и употребление"),
    (classes["10А"], teachers["История"],         subjects["История"],         7,  "Великая Отечественная война: основные этапы"),
    (classes["5Б"],  teachers["Математика"],      subjects["Математика"],      1,  "Дроби и их свойства"),
    (classes["5Б"],  teachers["История"],         subjects["История"],         5,  "Древний Египет"),
    (classes["7Г"],  teachers["Математика"],      subjects["Математика"],      2,  "Квадратные уравнения"),
    (classes["7Г"],  teachers["Русский язык"],    subjects["Русский язык"],    6,  "Причастие как часть речи"),
    (classes["9А"],  teachers["Физика"],          subjects["Физика"],          3,  "Законы Ньютона"),
    (classes["9А"],  teachers["Русский язык"],    subjects["Русский язык"],    8,  "Сложноподчинённые предложения"),
    (classes["1В"],  teachers["Английский язык"], subjects["Английский язык"], 1,  "Алфавит и базовые слова"),
    (classes["1В"],  teachers["Математика"],      subjects["Математика"],      9,  "Счёт до 20"),
]
lessons = []
for class_id, teacher_id, subject_id, day_offset, topic in lesson_defs:
    lesson_date = (TODAY + timedelta(days=day_offset)).isoformat()
    r = post("/lessons/", admin_token, {
        "class_id": class_id, "teacher_id": teacher_id, "subject_id": subject_id,
        "date": lesson_date, "topic": topic,
    })
    if r.status_code == 201:
        lessons.append(r.json())

print("lessons created:", len(lessons))

# class_id -> [student_id]
class_students = {}
for email, (sid, cls) in students.items():
    class_students.setdefault(classes[cls], []).append(sid)
class_students.setdefault(classes["10А"], []).append(student_anton["id"])

# ── Grades + Attendances ──────────────────────────────────────────────────────
grade_cycle = [5, 4, 3, 5, 4]
att_cycle = ["present", "present", "late", "present", "absent"]
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

print("grades/attendances created")

# ── Notifications ──────────────────────────────────────────────────────────────
notif_targets = [student_anton["id"]] + [students[e][0] for e in students]
for idx, sid in enumerate(notif_targets[:6]):
    post("/notifications/", admin_token, {
        "recipient_id": sid,
        "title": "Добро пожаловать в Зурнал",
        "body": "Ваш аккаунт активирован. Следите за расписанием уроков и оценками в системе.",
    })

print("done")
