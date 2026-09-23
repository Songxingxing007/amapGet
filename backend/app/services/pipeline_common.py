"""Shared retry and key-rotation helper for both pipelines."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

import httpx

from app.services.amap_client import AmapClient, AmapError
from app.services.keypool import KeyPool, Pacer

RETRY_BUCKETS = {"rate_limited", "retryable"}
PAUSE_BUCKETS = {"no_key", "exhausted_retries", "quota_exhausted", "insufficient_privileges", "key_invalid"}
MAX_ATTEMPTS = 5


def pause_reason(bucket: str | None) -> str:
    if bucket == "no_key":
        return "\u6240\u6709 Key \u90fd\u4e0d\u53ef\u7528\uff0c\u8bf7\u68c0\u67e5\u914d\u7f6e"
    if bucket == "key_invalid":
        return "Key \u65e0\u6548\uff0c\u8bf7\u5728\u914d\u7f6e\u9875\u66f4\u65b0"
    if bucket == "insufficient_privileges":
        return "Key \u6743\u9650\u4e0d\u8db3\uff1aAOI \u8fb9\u754c\u67e5\u8be2\u9700\u63d0\u5de5\u5355\u5f00\u901a"
    return "\u65e5\u914d\u989d\u8017\u5c3d\u6216\u91cd\u8bd5\u7528\u5c3d\uff0c\u53ef\u6b21\u65e5\u7eed\u8dd1"


async def call_with_key(
    action: Callable[[AmapClient], Awaitable[object]],
    pool: KeyPool,
    pacer: Pacer,
    http: httpx.AsyncClient,
    region: str,
) -> tuple[object | None, str | None]:
    """Run one request, rotating keys and backing off on transient failures."""
    attempts = 0
    while attempts < MAX_ATTEMPTS:
        key = pool.acquire()
        if key is None:
            return None, pool.last_reason or "no_key"
        await pacer.wait()
        client = AmapClient(key, http, region)
        try:
            result = await action(client)
            pool.release(key)
            return result, None
        except AmapError as exc:
            pool.penalize(key, exc.bucket)
            if exc.bucket in {"quota_exhausted"} | RETRY_BUCKETS:
                attempts += 1
                if exc.bucket in RETRY_BUCKETS:
                    await asyncio.sleep(min(2.0**attempts, 10.0))
                continue
            return None, exc.bucket
        except httpx.HTTPError:
            attempts += 1
            await asyncio.sleep(min(2.0**attempts, 10.0))
    return None, "exhausted_retries"
