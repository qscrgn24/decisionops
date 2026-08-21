import math
import time
from collections.abc import Callable
from dataclasses import dataclass
from threading import Lock


@dataclass(frozen=True)
class RateLimitPolicy:
    name: str
    requests: int
    window_seconds: int

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Rate-limit policy name is required.")

        if self.requests < 1:
            raise ValueError("Rate-limit request count must be at least 1.")

        if self.window_seconds < 1:
            raise ValueError("Rate-limit window must be at least 1 second.")

    @property
    def refill_rate(self) -> float:
        return self.requests / self.window_seconds


@dataclass
class _Bucket:
    tokens: float
    updated_at: float
    last_seen_at: float


class RateLimitExceeded(Exception):
    def __init__(self, *, retry_after_seconds: int) -> None:
        self.retry_after_seconds = retry_after_seconds

        super().__init__("Rate limit Exceeded.")


class TokenBucketRateLimiter:
    def __init__(self, *, max_buckets: int, clock: Callable[[], float] = time.monotonic) -> None:
        if max_buckets < 1:
            raise ValueError("max_buckets must be at least 1.")

        self.max_buckets = max_buckets
        self._clock = clock
        self._lock = Lock()
        self._buckets: dict[str, _Bucket] = {}

    def check(self, *, identity: str, policy: RateLimitPolicy) -> None:
        if not identity:
            raise ValueError("Rate-limit identity is required.")

        now = self._clock()
        bucket_key = self._bucket_key(identity=identity, policy=policy)

        with self._lock:
            bucket = self._buckets.get(bucket_key)

            if bucket is None:
                self._make_room(now=now)
                self._buckets[bucket_key] = _Bucket(tokens=float(policy.requests - 1), updated_at=now, last_seen_at=now)

                return

            available_tokens = self._refilled_tokens(bucket=bucket, policy=policy, now=now)
            bucket.updated_at = now
            bucket.last_seen_at = now

            if available_tokens >= 1.0:
                bucket.tokens = available_tokens - 1.0

                return

            bucket.tokens = available_tokens

            retry_after = self._retry_after_seconds(available_tokens=available_tokens, policy=policy)

            raise RateLimitExceeded(retry_after_seconds=retry_after)

    def _make_room(self, *, now: float) -> None:
        if len(self._buckets) < self.max_buckets:
            return

        self._remove_inactive_buckets(now=now)

        if len(self._buckets) < self.max_buckets:
            return

        oldest_key = min(self._buckets, key=lambda key: self._buckets[key].last_seen_at)
        del self._buckets[oldest_key]

    def _remove_inactive_buckets(self, *, now: float) -> None:
        removable: list[str] = []

        for key, bucket in self._buckets.items():
            policy_window = self._policy_window_from_key(key)
            if now - bucket.last_seen_at >= policy_window:
                removable.append(key)

        for key in removable:
            del self._buckets[key]

    @staticmethod
    def _bucket_key(*, identity: str, policy: RateLimitPolicy) -> str:
        return (
            f"{policy.name}:"
            f"{policy.requests}:"
            f"{policy.window_seconds}:"
            f"{identity}"
        )

    @staticmethod
    def _policy_window_from_key(bucket_key: str) -> int:
        parts = bucket_key.split(":", maxsplit=3)

        if len(parts) != 4:
            return 1

        try:
            return int(parts[2])
        except ValueError:
            return 1

    @staticmethod
    def _refilled_tokens(*, bucket: _Bucket, policy: RateLimitPolicy, now: float) -> float:
        elapsed = max(0.0, now - bucket.updated_at)
        refilled = bucket.tokens + elapsed * policy.refill_rate

        return min(float(policy.requests), refilled)

    @staticmethod
    def _retry_after_seconds(*, available_tokens: float, policy: RateLimitPolicy) -> int:
        missing_tokens = max(0.0, 1.0 - available_tokens)
        seconds = missing_tokens / policy.refill_rate

        return max(1, math.ceil(seconds))
