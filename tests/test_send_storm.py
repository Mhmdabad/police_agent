from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
import pytest
from cop_agent.infra.dos_detector import Detector, DosDetected
from cop_agent.infra.gatekeeper import Gatekeeper, Rejected
from cop_agent.infra.quota import Quota
from cop_agent.infra.report import Message, Report, Repositories, SubGameResult
from cop_agent.infra.token_bucket import Limiter, TokenBucket
STORM = 4000
"""Iterations of the loop. A bug does not get bored."""
class Clock:
    def __init__(self, at: float = 1000.0, step: float = 0.002) -> None:
        self.at = at
        self.step = step
    def __call__(self) -> float:
        self.at += self.step
        return self.at
@dataclass
class CountingApi:
    calls: list[dict[str, str]] = field(default_factory=list)
    def send(self, payload: dict[str, str]) -> None:
        self.calls.append(payload)
    @property
    def count(self) -> int:
        return len(self.calls)
def a_report() -> Report:
    return Report(
        game_id="uoh26-s82kma9e",
        role="police",
        team="uoh26-cops",
        opponent_team="uoh26-others",
        repositories=Repositories(
            cop_repo="https://github.com/Mhmdabad/police_agent",
            thief_repo="https://github.com/Mhmdabad/theif_agent",
            opponent_cop_repo="https://github.com/other/police",
            opponent_thief_repo="https://github.com/other/thief",
        ),
        sub_games=(SubGameResult(sub_game=1, cop_score=100, thief_score=0, commit_hash="a" * 40),),
        total_tokens=1234,
        agreed=True,
    )
def gatekeeper(tmp_path: Path, clock: Clock, limit: int = 50) -> Gatekeeper:
    return Gatekeeper(
        detector=Detector(path=tmp_path / ".locked_cop.json", now=clock),
        quota=Quota(path=tmp_path / ".quota_cop.json", limit=limit, now=lambda: datetime.now(UTC)),
        limiter=Limiter(bucket=TokenBucket(capacity=2.0, per_minute=30.0, now=clock)),
    )
@dataclass
class Storm:
    attempts: int = 0
    sent: int = 0
    stopped_by: str = ""
def run_storm(gate: Gatekeeper, api: CountingApi, iterations: int = STORM) -> Storm:
    storm = Storm()
    payload = Message(report=a_report(), sender="cop@example.com").raw()
    for _ in range(iterations):
        storm.attempts += 1
        try:
            waited = gate.admit()
            if waited is not None:
                gate.release()
                continue
            gate.record_attempt()
            api.send(payload)
            storm.sent += 1
        except (Rejected, DosDetected) as exc:
            storm.stopped_by = type(exc).__name__
            return storm
    return storm
