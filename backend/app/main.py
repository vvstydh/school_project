from fastapi import FastAPI

import app.models  # noqa: F401 — регистрирует все ORM модели в Base.metadata

from app.core.logger import logger
from app.middleware import LoggingMiddleware
from app.routers import auth, users, subjects, classes, lessons, grades, attendances, notifications

app = FastAPI(title="Школьный журнал", version="1.0.0")

app.add_middleware(LoggingMiddleware)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(subjects.router)
app.include_router(classes.router)
app.include_router(lessons.router)
app.include_router(grades.router)
app.include_router(attendances.router)
app.include_router(notifications.router)


@app.on_event("startup")
async def on_startup():
    logger.info("=" * 60)
    logger.info("Приложение запущено")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def on_shutdown():
    logger.info("Приложение остановлено")


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
