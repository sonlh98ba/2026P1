import asyncio
import os
from contextlib import suppress

from fastapi import FastAPI
from app.api.dashboard import router as dashboard_router
from fastapi.middleware.cors import CORSMiddleware
from .core.pipeline import run_pipeline
from .database import engine
from .models import Base

PIPELINE_SCAN_INTERVAL_SECONDS = int(os.getenv("PIPELINE_SCAN_INTERVAL_SECONDS", "300"))
PIPELINE_SCAN_LIMIT = int(os.getenv("PIPELINE_SCAN_LIMIT", "50"))

app = FastAPI(title="AIOps Platform")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard"])


async def _pipeline_scan_job():
    while True:
        try:
            stats = await asyncio.to_thread(run_pipeline, PIPELINE_SCAN_LIMIT)
            print(f"[pipeline-job] scan done: {stats}")
        except Exception as exc:
            print(f"[pipeline-job] scan failed: {exc}")
        await asyncio.sleep(PIPELINE_SCAN_INTERVAL_SECONDS)


@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)
    app.state.pipeline_task = asyncio.create_task(_pipeline_scan_job())
    print(
        f"AIOps Platform started (pipeline scan each {PIPELINE_SCAN_INTERVAL_SECONDS}s)"
    )


@app.on_event("shutdown")
async def shutdown():
    task = getattr(app.state, "pipeline_task", None)
    if task:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


@app.get("/health")
def health():
    return {"status": "ok"}
