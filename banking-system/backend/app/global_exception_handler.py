import traceback
from fastapi import Request
from fastapi.responses import JSONResponse
from .audit import audit_log


async def global_exception_handler(request: Request, exc: Exception):
    stack = traceback.format_exc()

    audit_log(
        action="SYSTEM_ERROR",
        api=str(request.url.path),
        method=request.method,
        status="FAILED",
        error=str(exc),
        error_type=type(exc).__name__,
        stacktrace=stack,
        http_status=500
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error",
            "trace_id": "logged"
        }
    )
