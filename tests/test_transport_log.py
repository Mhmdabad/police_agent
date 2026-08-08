import re
from pathlib import Path
import pytest
from cop_agent.infra.mcp_client import ClientSettings, OpponentClient, OpponentUnreachableError
from cop_agent.infra.transport_log import (
    CONNECT,
    KINDS,
    RECONNECT,
    RETRY,
    SENT,
    TIMEOUT,
    UNREACHABLE,
    Event,
    TransportLog,
    now_utc,
)
from cop_agent.shared.naming import NamingError, transport_log_filename
URL = "https://opponent-c3d4.ngrok-free.app/mcp"
MOVED = "https://opponent-e5f6.ngrok-free.app/mcp"
class Ticking:
    def __init__(self) -> None:
        self.reads = 0
    def __call__(self) -> str:
        self.reads += 1
        return f"2026-08-04T09:00:00.{self.reads:03d}+00:00"
class Flaky:
    def __init__(self, *outcomes: object) -> None:
        self._outcomes = list(outcomes)
    def call(
        self, url: str, tool: str, payload: dict[str, object], timeout: float
    ) -> dict[str, object]:
        outcome = self._outcomes.pop(0) if self._outcomes else {"ok": True}
        if isinstance(outcome, Exception):
            raise outcome
        assert isinstance(outcome, dict)
        return outcome
def client(*outcomes: object, url: str = URL) -> OpponentClient:
    settings = ClientSettings(opponent_url=url, retry_backoff_sec=0.0)
    return OpponentClient(Flaky(*outcomes), settings, log=TransportLog(clock=Ticking()))
