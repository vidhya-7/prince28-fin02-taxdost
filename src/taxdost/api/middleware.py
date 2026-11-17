"""Gives every request an ID, logs it, and turns crashes into a clean 500."""

import logging
import time
import uuid

from fastapi import Request, Response

from taxdost.api.errors import problem_response
from taxdost.logging_setup import request_id_ctx

logger = logging.getLogger("taxdost.http")


async def request_context(request: Request, call_next) -> Response:
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:16]
    token = request_id_ctx.set(request_id)
    start = time.perf_counter()
    try:
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("unhandled error")
            response = problem_response(
                request, 500, "Something went wrong on our side. Quote the request ID."
            )
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request finished",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round((time.perf_counter() - start) * 1000, 1),
            },
        )
        return response
    finally:
        request_id_ctx.reset(token)
