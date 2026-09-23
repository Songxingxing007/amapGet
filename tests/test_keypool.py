import pytest

from app.services.keypool import KeyPool, Pacer


def test_rotation_and_disabling():
    pool = KeyPool(["a", "b"], daily_limit_per_key=10)
    assert pool.acquire() == "a"
    assert pool.acquire() == "b"
    pool.penalize("a", "key_invalid")
    assert pool.acquire() == "b"
    assert pool.disabled() == ["a"]


def test_daily_limit_marks_key_exhausted():
    pool = KeyPool(["a"], daily_limit_per_key=2)
    pool.release("a")
    pool.release("a")
    assert pool.acquire() is None
    assert pool.all_exhausted is True


def test_quota_error_consumes_the_key():
    pool = KeyPool(["a", "b"], daily_limit_per_key=5)
    pool.penalize("a", "quota_exhausted")
    assert pool.acquire() == "b"
    assert pool.usage()["a"] == 5


@pytest.mark.asyncio
async def test_pacer_rests_every_n_calls():
    slept: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        slept.append(seconds)

    pacer = Pacer(qps=0, sleep_every=3, sleep_min=3.0, sleep_max=8.0, sleeper=fake_sleep)
    for _ in range(7):
        await pacer.wait()
    rests = [value for value in slept if value >= 3.0]
    assert len(slept) == 2
    assert all(3.0 <= rest <= 8.0 for rest in rests)
