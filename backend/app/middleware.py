import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logger import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start = time.perf_counter()

        logger.info(
            f"[{request_id}] → {request.method} {request.url.path}"
            + (f"?{request.url.query}" if request.url.query else "")
        )

        try:
            response = await call_next(request)
        except Exception as exc:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error(f"[{request_id}] ✗ {request.method} {request.url.path} — EXCEPTION {exc!r} ({elapsed:.1f}ms)")
            raise

        elapsed = (time.perf_counter() - start) * 1000
        level = logger.warning if response.status_code >= 400 else logger.info
        level(
            f"[{request_id}] ← {response.status_code} {request.method} {request.url.path} ({elapsed:.1f}ms)"
        )

        return response
