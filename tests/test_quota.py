import json
import stat
from datetime import UTC, datetime, timedelta
from pathlib import Path
import pytest
from cop_agent.infra.quota import (
    DAILY_LIMIT,
    QUOTA_PATH_ENV,
    Quota,
    QuotaError,
    QuotaExhausted,
    quota_path,
)
NOON = datetime(2026, 8, 5, 12, 0, tzinfo=UTC)
class Clock:
    def __init__(self, at: datetime = NOON) -> None:
        self.at = at
    def __call__(self) -> datetime:
        return self.at
    def advance(self, **delta: float) -> None:
        self.at += timedelta(**delta)
def quota(tmp_path: Path, limit: int = 3, clock: Clock | None = None) -> Quota:
    return Quota(path=tmp_path / ".quota_cop.json", limit=limit, now=clock or Clock())
