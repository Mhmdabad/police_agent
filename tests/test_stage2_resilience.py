import pytest
from cop_agent.domain.outcome import TechnicalLoss
from cop_agent.infra.inboxes import PeerInboxes
from cop_agent.infra.mcp_client import ClientSettings, OpponentClient
from cop_agent.runtime.deadline import DeadlineExpiredError, DeadlineTracker
from cop_agent.runtime.orchestrator import MatchAborted, Orchestrator
from cop_agent.runtime.scheduler import OutOfTurnError, TurnScheduler
from cop_agent.runtime.state_machine import (
    GamePhaseMachine,
    IllegalTransitionError,
    Phase,
)
from cop_agent.runtime.watchdog import Watchdog, WatchdogVerdict
SETTINGS = ClientSettings(opponent_url="http://127.0.0.1:8802/mcp", retry_backoff_sec=0.0)
class FakeClock:
    def __init__(self, now: float = 100.0) -> None:
        self.now = now
    def __call__(self) -> float:
        return self.now
    def advance(self, seconds: float) -> None:
        self.now += seconds
class DeadTransport:
    def __init__(self, alive_calls: int = 0) -> None:
        self.remaining = alive_calls
        self.calls = 0
    def call(
        self, url: str, tool: str, payload: dict[str, object], timeout: float
    ) -> dict[str, object]:
        self.calls += 1
        if self.remaining > 0:
            self.remaining -= 1
            return {"ok": True, "data": {}}
        raise ConnectionError("peer went away")
def orchestrator(transport: DeadTransport) -> Orchestrator:
    return Orchestrator(PeerInboxes(), OpponentClient(transport, SETTINGS))
