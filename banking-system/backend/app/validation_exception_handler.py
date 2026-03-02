from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from .audit import audit_log


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    audit_log(
        action="VALIDATION_ERROR",
        api=str(request.url.path),
        method=request.method,
        status="FAILED",
        error="Request validation failed",
        error_type="RequestValidationError",
        validation_errors=exc.errors(),
        http_status=422
    )

    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )
