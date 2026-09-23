"""Key rotation, per-key daily counters and request pacing."""

from __future__ import annotations

import asyncio
import random
import time
from collections.abc import Awaitable, Callable

DISABLING_REASONS = {"key_invalid", "insufficient_privileges"}


class KeyPool:
    """Rotate keys, skip disabled or exhausted ones, remember usage."""

    def __init__(self, keys: list[str], daily_limit_per_key: int) -> None:
        self._keys = [key for key in keys if key]
        self._limit = max(1, daily_limit_per_key)
        self._used: dict[str, int] = {key: 0 for key in self._keys}
        self._disabled: set[str] = set()
        self._cursor = 0
        self.last_reason: str | None = None

    @property
    def keys(self) -> list[str]:
        return list(self._keys)

    def acquire(self) -> str | None:
        total = len(self._keys)
        for _ in range(total):
            key = self._keys[self._cursor % total]
            self._cursor += 1
            if key in self._disabled:
                continue
            if self._used.get(key, 0) >= self._limit:
                continue
            return key
        return None

    def release(self, key: str) -> None:
        self._used[key] = self._used.get(key, 0) + 1

    def penalize(self, key: str, reason: str) -> None:
        self.last_reason = reason
        if reason in DISABLING_REASONS:
            self._disabled.add(key)
        elif reason == "quota_exhausted":
            self._used[key] = self._limit

    @property
    def all_exhausted(self) -> bool:
        return self.acquire() is None

    def usage(self) -> dict[str, int]:
        return dict(self._used)

    def disabled(self) -> list[str]:
        return sorted(self._disabled)


class Pacer:
    """Global QPS limit plus a random rest every N requests."""

    def __init__(
        self,
        qps: float = 3.0,
        sleep_every: int = 20,
        sleep_min: float = 3.0,
        sleep_max: float = 8.0,
        sleeper: Callable[[float], Awaitable[None]] | None = None,
    ) -> None:
        self.qps = qps
        self.sleep_every = max(0, sleep_every)
        self.sleep_min = max(0.0, sleep_min)
        self.sleep_max = max(self.sleep_min, sleep_max)
        self._sleep = sleeper or asyncio.sleep
        self._calls = 0
        self._last = 0.0
        self.sleeps: list[float] = []

    async def wait(self) -> None:
        if self.qps and self.qps > 0:
            interval = 1.0 / self.qps
            now = time.monotonic()
            delay = self._last + interval - now
            if self._last and delay > 0:
                self.sleeps.append(delay)
                await self._sleep(delay)
            self._last = time.monotonic()
        self._calls += 1
        if self.sleep_every and self._calls % self.sleep_every == 0:
            rest = random.uniform(self.sleep_min, self.sleep_max)
            self.sleeps.append(rest)
            await self._sleep(rest)
