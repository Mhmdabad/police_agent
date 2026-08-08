"""Gate two: the token bucket, and the queue in front of it.

TokenBucket and Limiter classes for rate limiting.
"""

import time
from collections.abc import Callable
from dataclasses import dataclass, field

from ..shared.appendix_f import book_value

SECTION = "rate_limiter_gatekeeper"


def _minimum(key: str) -> int:
    value = book_value(SECTION, key)
    if not isinstance(value, int):  # pragma: no cover - the table is typed
        raise TypeError(f"{SECTION}.{key} is not an integer: {value!r}")
    return value


REQUESTS_PER_MINUTE = _minimum("requests_per_minute")
CONCURRENT_REQUESTS = _minimum("concurrent_requests")
RETRY_BACKOFF_SEC = _minimum("retry_backoff_sec")
MAX_RETRIES = _minimum("max_retries")
QUEUE_DEPTH = _minimum("queue_depth")


class RateLimitError(RuntimeError):
    """Raised when a request cannot proceed under the configured limits."""


class QueueFull(RateLimitError):
    """Raised when the waiting queue is at capacity — backpressure, not an error."""


@dataclass
class TokenBucket:
    """``tokens ← min(C, tokens + r·Δt)``, evaluated on demand."""

    capacity: float = float(CONCURRENT_REQUESTS)
    per_minute: float = float(REQUESTS_PER_MINUTE)
    now: Callable[[], float] = field(default=time.monotonic)
    _tokens: float = field(default=-1.0, init=False, repr=False)
    _updated: float = field(default=0.0, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.per_minute < REQUESTS_PER_MINUTE:
            raise RateLimitError(
                f"requests_per_minute is a minimum in Appendix F ({REQUESTS_PER_MINUTE}); "
                f"{self.per_minute} is below it, and a *minimum* parameter that drifts "
                "downward is a deviation the audit catches"
            )
        if self.capacity < CONCURRENT_REQUESTS:
            raise RateLimitError(
                f"concurrent_requests is a minimum in Appendix F ({CONCURRENT_REQUESTS}); "
                f"a burst capacity of {self.capacity} is below it"
            )
        self._tokens = self.capacity
        self._updated = self.now()

    @property
    def rate(self) -> float:
        """``r`` — tokens per second."""
        return self.per_minute / 60.0

    def _refill(self) -> None:
        moment = self.now()
        elapsed = max(moment - self._updated, 0.0)
        self._tokens = min(self.capacity, self._tokens + self.rate * elapsed)
        self._updated = moment

    def tokens(self) -> float:
        """How much burst is available right now."""
        self._refill()
        return self._tokens

    def allow(self) -> bool:
        """``allow ⟺ tokens ≥ 1``. Spends a token when it returns ``True``."""
        self._refill()
        if self._tokens < 1.0:
            return False
        self._tokens -= 1.0
        return True

    def wait_for(self) -> float:
        """Seconds until one token is available. Zero when a request may go now.

        Returned rather than slept. A module that slept could not be tested
        without a test that also slept, and the caller is better placed to
        decide whether to wait, queue or give up.
        """
        self._refill()
        if self._tokens >= 1.0:
            return 0.0
        return (1.0 - self._tokens) / self.rate


@dataclass
class Limiter:
    """The bucket plus the bounded queue the rulebook asks for."""

    bucket: TokenBucket = field(default_factory=TokenBucket)
    queue_depth: int = QUEUE_DEPTH
    max_retries: int = MAX_RETRIES
    backoff_sec: float = float(RETRY_BACKOFF_SEC)
    waiting: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        for name, value, floor in (
            ("queue_depth", self.queue_depth, QUEUE_DEPTH),
            ("max_retries", self.max_retries, MAX_RETRIES),
            ("retry_backoff_sec", self.backoff_sec, RETRY_BACKOFF_SEC),
        ):
            if value < floor:
                raise RateLimitError(
                    f"{name} is a minimum in Appendix F ({floor}); {value} is below it"
                )

    def enter(self) -> float:
        """Join the queue. Returns the seconds to wait before sending."""
        if self.waiting >= self.queue_depth:
            raise QueueFull(
                f"{self.waiting} requests already waiting, queue depth is {self.queue_depth}; "
                "refusing rather than growing, because an unbounded queue turns a rate "
                "problem into a memory problem and hides it until the process dies"
            )
        delay = self.bucket.wait_for()
        if delay == 0.0:
            self.bucket.allow()
            return 0.0
        self.waiting += 1
        return delay

    def leave(self) -> None:
        """Release a queued slot once the caller has stopped waiting."""
        self.waiting = max(self.waiting - 1, 0)

    def backoff_for(self, attempt: int) -> float:
        """Seconds to wait before retry number ``attempt`` (1-based)."""
        if attempt < 1:
            raise RateLimitError(f"attempts are numbered from 1, got {attempt}")
        if attempt > self.max_retries:
            raise RateLimitError(
                f"{self.max_retries} retries exhausted; there is no further attempt, "
                "because insisting is what gets an account suspended"
            )
        return self.backoff_sec * (2.0 ** (attempt - 1))
