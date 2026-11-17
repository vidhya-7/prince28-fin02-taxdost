"""Every error leaves the API in one shape: RFC 9457 problem details."""

from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from taxdost.logging_setup import request_id_ctx

PROBLEM_JSON = "application/problem+json"


def problem_response(request: Request, status: int, detail: str, **extra: object) -> JSONResponse:
    body = {
        "type": "about:blank",
        "title": HTTPStatus(status).phrase,
        "status": status,
        "detail": detail,
        "instance": request.url.path,
        "request_id": request_id_ctx.get(),
        **extra,
    }
    return JSONResponse(body, status_code=status, media_type=PROBLEM_JSON)


async def http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return problem_response(request, exc.status_code, str(exc.detail))


async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = [{"field": ".".join(map(str, e["loc"])), "msg": e["msg"]} for e in exc.errors()]
    return problem_response(request, 422, "Some request values are invalid.", errors=errors)


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, http_error)
    app.add_exception_handler(RequestValidationError, validation_error)
