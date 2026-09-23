"""Engine and initialisation helpers."""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import event
from sqlmodel import SQLModel, create_engine

from app.db import models  # noqa: F401  (registers tables on SQLModel.metadata)


def db_path() -> Path:
    data_dir = os.environ.get("DATA_DIR")
    base = Path(data_dir) if data_dir else Path("data")
    return base / "app.db"


def get_engine():
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{path.as_posix()}", connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _set_wal(dbapi_conn, _record):  # pragma: no cover - trivial pragma
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

    return engine


def init_db() -> None:
    SQLModel.metadata.create_all(get_engine())
