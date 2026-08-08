from pathlib import Path
from typing import Any
import pytest
from cop_agent.infra.token_bucket import (
    CONCURRENT_REQUESTS,
    MAX_RETRIES,
    QUEUE_DEPTH,
    REQUESTS_PER_MINUTE,
    RETRY_BACKOFF_SEC,
    Limiter,
    QueueFull,
    RateLimitError,
    TokenBucket,
)
from cop_agent.shared.appendix_f import book_value
class Clock:
    def __init__(self, at: float = 1000.0) -> None:
        self.at = at
    def __call__(self) -> float:
        return self.at
    def advance(self, seconds: float) -> None:
        self.at += seconds
def bucket(
    clock: Clock | None = None, capacity: float = 2.0, per_minute: float = 30.0
) -> TokenBucket:
    return TokenBucket(capacity=capacity, per_minute=per_minute, now=clock or Clock())
