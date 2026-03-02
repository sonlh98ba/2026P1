from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from .audit import audit_log


async def http_exception_handler(request: Request, exc: HTTPException):
    audit_log(
        action="BUSINESS_ERROR",
        api=str(request.url.path),
        method=request.method,
        status="FAILED",
        error=str(exc.detail),
        error_type="HTTPException",
        http_status=exc.status_code
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )
