"""FastAPI application entry point."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import config, records, tasks

app = FastAPI(title="Amap POI/AOI Collector", version="0.1.0")


def resolve_dist() -> Path | None:
    """Find frontend/dist both when running from source and from a frozen exe."""
    candidates: list[Path] = []
    bundle = getattr(sys, "_MEIPASS", None)
    if bundle:
        candidates.append(Path(bundle) / "frontend" / "dist")
    candidates.append(Path(__file__).resolve().parents[2] / "frontend" / "dist")
    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).resolve().parent / "frontend" / "dist")
    for candidate in candidates:
        if (candidate / "index.html").exists():
            return candidate
    return None


# Only for the Vite dev server; production is same-origin so no CORS is needed.
if os.environ.get("DEV") == "1":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(config.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(records.router, prefix="/api")


@app.get("/api/health")
def health() -> dict[str, str]:
    """Liveness probe used by the frontend and by tests."""
    return {"status": "ok"}


DIST_DIR = resolve_dist()
if DIST_DIR is not None:
    app.mount("/", StaticFiles(directory=DIST_DIR, html=True), name="spa")
