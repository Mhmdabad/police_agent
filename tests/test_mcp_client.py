import dataclasses
import tomllib
from pathlib import Path
from typing import Any
import pytest
from cop_agent.infra.mcp_client import (
    OPPONENT_URL_ENV,
    ClientSettings,
    OpponentClient,
    OpponentUnreachableError,
)
SETTINGS = ClientSettings(opponent_url="http://127.0.0.1:8802/mcp", retry_backoff_sec=0.0)
REMOTE = "https://opponent-c3d4.ngrok-free.app"
class FakeTransport:
    def __init__(self, *outcomes: object) -> None:
        self._outcomes = list(outcomes)
        self.calls: list[dict[str, Any]] = []
    def call(self, url: str, tool: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
        self.calls.append({"url": url, "tool": tool, "payload": payload, "timeout": timeout})
        outcome = self._outcomes.pop(0) if self._outcomes else {"ok": True}
        if isinstance(outcome, Exception):
            raise outcome
        assert isinstance(outcome, dict)
        return outcome
class MutatingTransport:
    def __init__(self, failures: int) -> None:
        self.failures = failures
        self.seen: list[dict[str, Any]] = []
    def call(self, url: str, tool: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
        self.seen.append(dict(payload))
        payload["move"] = "TAMPERED"
        payload.setdefault("trace", []).append(len(self.seen))
        if self.failures > 0:
            self.failures -= 1
            raise TimeoutError("no answer")
        return {"ok": True}
