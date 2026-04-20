from fastapi import FastAPI

import app.models  # noqa: F401 — регистрирует все ORM модели в Base.metadata

from app.routers import auth, users, subjects, classes, lessons, grades, attendances, notifications

app = FastAPI(title="Школьный журнал", version="1.0.0")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(subjects.router)
app.include_router(classes.router)
app.include_router(lessons.router)
app.include_router(grades.router)
app.include_router(attendances.router)
app.include_router(notifications.router)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
