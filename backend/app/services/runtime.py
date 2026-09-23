"""In-process task registry so the API can pause and resume pipelines."""

from __future__ import annotations

import asyncio

RUNNING: dict[int, asyncio.Task] = {}
PAUSED: set[int] = set()


def pause(task_id: int) -> None:
    PAUSED.add(task_id)


def resume(task_id: int) -> None:
    PAUSED.discard(task_id)


def is_paused(task_id: int) -> bool:
    return task_id in PAUSED


def track(task_id: int, task: asyncio.Task) -> None:
    RUNNING[task_id] = task
    task.add_done_callback(lambda _: RUNNING.pop(task_id, None))
