import json
from datetime import UTC, datetime
from pathlib import Path
import pytest
from cop_agent.infra.dos_detector import Detector
from cop_agent.infra.gatekeeper import (
    TOO_MANY_REQUESTS,
    Gatekeeper,
    Rejected,
    TooManyRequests,
    Wait,
    status_code_of,
)
from cop_agent.infra.quota import Quota, QuotaError
from cop_agent.infra.token_bucket import Limiter, RateLimitError, TokenBucket
class Clock:
    def __init__(self, at: float = 1000.0) -> None:
        self.at = at
    def __call__(self) -> float:
        return self.at
    def advance(self, seconds: float) -> None:
        self.at += seconds
def gatekeeper(tmp_path: Path, limit: int = 10, capacity: float = 2.0) -> Gatekeeper:
    clock = Clock()
    return Gatekeeper(
        detector=Detector(path=tmp_path / ".locked_cop.json", now=clock),
        quota=Quota(path=tmp_path / ".quota_cop.json", limit=limit, now=lambda: datetime.now(UTC)),
        limiter=Limiter(bucket=TokenBucket(capacity=capacity, per_minute=30.0, now=clock)),
    )
