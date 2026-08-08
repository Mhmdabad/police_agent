from pathlib import Path
from typing import Any
import pytest
from cop_agent.domain.outcome import TechnicalLoss, technical_loss_scores
from cop_agent.infra.inboxes import PeerInboxes
from cop_agent.infra.mcp_client import ClientSettings, OpponentClient
from cop_agent.infra.transport_log import CONNECT, RETRY, SENT, TIMEOUT, UNREACHABLE, TransportLog
from cop_agent.runtime.deadline import DEFAULT_RESPONSE_TIMEOUT_SEC
from cop_agent.runtime.orchestrator import MatchAborted, Orchestrator
from cop_agent.runtime.state_machine import GamePhaseMachine, Phase
from cop_agent.runtime.watchdog import DEFAULT_WATCHDOG_TIMEOUT_SEC, Watchdog, WatchdogVerdict
LIVE_URL = "https://opponent-c3d4.ngrok-free.app/mcp"
TURN = {
    "step": 4,
    "sender": "thief",
    "hint": "gone quiet",
    "smell_grid": {"3,3": 0.9},
    "commit": "a" * 64,
    "timestamp": "2026-08-04T09:00:00+00:00",
}
class Tunnel:
    def __init__(self, elapsed: list[float] | None = None) -> None:
        self.alive = True
        self.calls = 0
        self.elapsed = elapsed if elapsed is not None else []
    def kill(self) -> None:
        self.alive = False
    def call(self, url: str, tool: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
        self.calls += 1
        if not self.alive:
            self.elapsed.append(timeout)  # a real drop can burn the whole window
            raise ConnectionError(f"tunnel at {url} is gone")
        return {"ok": True}
def peer(tunnel: Tunnel, slept: list[float] | None = None) -> Orchestrator:
    settings = ClientSettings(opponent_url=LIVE_URL)
    client = OpponentClient(
        tunnel,
        settings,
        sleep=(slept.append if slept is not None else (lambda _: None)),
        log=TransportLog(),
    )
    return Orchestrator(PeerInboxes(), client)
