import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
import pytest
from cop_agent.infra.dos_detector import Detector
from cop_agent.infra.gatekeeper import Gatekeeper
from cop_agent.infra.mailer import LECTURER_NOTE, Mailer, SendError, retry_after_of
from cop_agent.infra.quota import Quota
from cop_agent.infra.report import LECTURER, Report, Repositories, SubGameResult
from cop_agent.infra.token_bucket import Limiter, TokenBucket
REPOS = Repositories(
    cop_repo="https://github.com/Mhmdabad/police_agent",
    thief_repo="https://github.com/Mhmdabad/theif_agent",
    opponent_cop_repo="https://github.com/other/police",
    opponent_thief_repo="https://github.com/other/thief",
)
def a_report() -> Report:
    return Report(
        game_id="uoh26-s82kma9e",
        game_uid="u-0001",
        role="police",
        team="uoh26-cops",
        opponent_team="uoh26-others",
        repositories=REPOS,
        sub_games=(SubGameResult(sub_game=1, cop_score=100, thief_score=0, commit_hash="a" * 40),),
        total_tokens=1234,
        agreed=True,
    )
class Clock:
    def __init__(self, at: float = 1000.0) -> None:
        self.at = at
    def __call__(self) -> float:
        self.at += 0.001
        return self.at
class Resp:
    def __init__(self, headers: dict[str, object]) -> None:
        self.status = 429
        self.headers = headers
class TooMany(Exception):
    def __init__(self, retry_after: object | None = None) -> None:
        super().__init__("Too Many Requests")
        self.resp = Resp({"Retry-After": retry_after} if retry_after is not None else {})
@dataclass
class CountingApi:
    fail_with: list[Exception] = field(default_factory=list)
    calls: list[dict[str, str]] = field(default_factory=list)
    def send(self, raw: dict[str, str]) -> dict[str, Any]:
        self.calls.append(raw)
        if self.fail_with:
            raise self.fail_with.pop(0)
        return {"id": f"msg-{len(self.calls)}", "labelIds": ["SENT"]}
def a_mailer(
    tmp_path: Path, api: CountingApi | None = None, limit: int = 10, capacity: float = 2.0
) -> tuple[Mailer, CountingApi, Gatekeeper]:
    clock = Clock()
    gate = Gatekeeper(
        detector=Detector(path=tmp_path / ".locked_cop.json", now=clock),
        quota=Quota(path=tmp_path / ".quota_cop.json", limit=limit, now=lambda: datetime.now(UTC)),
        limiter=Limiter(bucket=TokenBucket(capacity=capacity, per_minute=30.0, now=clock)),
    )
    endpoint = api or CountingApi()
    slept: list[float] = []
    mailer = Mailer(gatekeeper=gate, sender=endpoint, sleep=slept.append)
    return mailer, endpoint, gate
