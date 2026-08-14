from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.services.rate_limit import RateLimitExceeded, RateLimitPolicy, TokenBucketRateLimiter


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def test_token_bucket_allows_burst_then_rejects() -> None:
    clock  = FakeClock()

    limiter = TokenBucketRateLimiter(max_buckets=10, clock=clock)
    policy = RateLimitPolicy(name="test", requests=2, window_seconds=10)

    limiter.check(identity="user:1", policy=policy)
    limiter.check(identity="user:1", policy=policy)

    with pytest.raises(RateLimitExceeded) as exc_info:
        limiter.check(identity="user:1", policy=policy)

    assert exc_info.value.retry_after_seconds == 5


def test_token_bucket_refills_over_time() -> None:
    clock = FakeClock()

    limiter = TokenBucketRateLimiter(max_buckets=10, clock=clock)
    policy = RateLimitPolicy(name="test", requests=2, window_seconds=10)

    limiter.check(identity="user:1", policy=policy)
    limiter.check(identity="user:1", policy=policy)

    with pytest.raises(RateLimitExceeded):
        limiter.check(identity="user:1", policy=policy)

    clock.advance(5.0)

    limiter.check(identity="user:1", policy=policy)


def test_rate_limit_identities_are_isolated() -> None:
    clock = FakeClock()
    
    limiter = TokenBucketRateLimiter(max_buckets=10, clock=clock)
    policy = RateLimitPolicy(name="test", requests=1, window_seconds=60)

    limiter.check(identity="user:1", policy=policy)

    with pytest.raises(RateLimitExceeded):
        limiter.check(identity="user:1", policy=policy)

    limiter.check(identity="user:2", policy=policy)


def test_rate_limit_policies_are_isolated() -> None:
    clock = FakeClock()

    limiter = TokenBucketRateLimiter(max_buckets=10, clock=clock)
    upload_policy = RateLimitPolicy(name="upload", requests=1, window_seconds=60)
    execute_policy = RateLimitPolicy(name="execute", requests=1, window_seconds=60)

    limiter.check(identity="user:1", policy=upload_policy)
    limiter.check(identity="user:1", policy=execute_policy)

    with pytest.raises(RateLimitExceeded):
        limiter.check(identity="user:1", policy=upload_policy)

    with pytest.raises(RateLimitExceeded):
        limiter.check(identity="user:1", policy=execute_policy)


def test_rate_limiter_bounds_bucket_storage() -> None:
    clock = FakeClock()

    limiter = TokenBucketRateLimiter(max_buckets=2, clock=clock)
    policy = RateLimitPolicy(name="test", requests=1, window_seconds=60)

    limiter.check(identity="ip:a", policy=policy)
    clock.advance(1.0)

    limiter.check(identity="ip:b", policy=policy)
    clock.advance(1.0)

    limiter.check(identity="ip:c", policy=policy)

    assert len(limiter._buckets) == 2 # noqa: SLF001

    # "ip:a" was the least recently used bucket and
    # should have been evicted, so it receives a fresh bucket.
    limiter.check(identity="ip:a", policy=policy)

    assert len(limiter._buckets) == 2 # noqa: SLF001


def test_rate_limiter_removes_inactive_buckets() -> None:
    clock = FakeClock()
    
    limiter = TokenBucketRateLimiter(max_buckets=2, clock=clock)
    policy = RateLimitPolicy(name="test", requests=1, window_seconds=60)

    limiter.check(identity="ip:a", policy=policy)
    limiter.check(identity="ip:b", policy=policy)

    clock.advance(60.0)

    limiter.check(identity="ip:c", policy=policy)

    assert len(limiter._buckets) == 1 # noqa: SLF001


def test_rate_limiter_is_thread_safe() -> None:
    clock = FakeClock()

    limiter = TokenBucketRateLimiter(max_buckets=10, clock=clock)
    policy = RateLimitPolicy(name="test", requests=5, window_seconds=60)

    def attemp_requests() -> bool:
        try:
            limiter.check(identity="user:1", policy=policy)
        except RateLimitExceeded:
            return False

        return True

    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(lambda _: attemp_requests(), range(20)))

    assert sum(results) == 5


def test_login_endpoint_returns_429_and_retry_after(client: TestClient) -> None:
    payload = {
        "identifier": "does-not-exist@example.com",
        "password": "IncorrectPassword123!", 
    }

    for _ in range(settings.LOGIN_RATE_LIMIT_REQUESTS):
        response = client.post("/api/auth/login", json=payload)

        assert response.status_code == 401

    blocked = client.post("/api/auth/login", json=payload)

    assert blocked.status_code == 429
    assert blocked.json() == {"detail": "Too many requests."}

    retry_after = blocked.headers.get("Retry-After")

    assert retry_after is not None
    assert int(retry_after) >= 1
