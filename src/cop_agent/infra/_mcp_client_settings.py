"""ClientSettings and exceptions for infra/mcp_client.py."""

import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from .tunnel import normalise

OPPONENT_URL_ENV = "OPPONENT_URL"
RETRY_KEY = "retry"


def deferred(answer: Mapping[str, Any]) -> bool:
    return answer.get("ok") is False and answer.get(RETRY_KEY) is True


class Transport(Protocol):
    def call(
        self, url: str, tool: str, payload: dict[str, Any], timeout: float
    ) -> dict[str, Any]: ...


class OpponentUnreachableError(RuntimeError):
    """Raised when the opponent could not be reached within the retry budget."""


class PeerNotReadyError(OpponentUnreachableError):
    """Raised when the opponent answered, but never opened its door in time."""


@dataclass(frozen=True, slots=True)
class ClientSettings:
    """How this peer talks to its opponent."""

    opponent_url: str
    response_timeout_sec: float = 30.0
    max_retries: int = 3
    retry_backoff_sec: float = 5.0

    def __post_init__(self) -> None:
        if not self.opponent_url.strip():
            raise ValueError("opponent_url must be set; it is all we know about the opponent")
        if self.response_timeout_sec <= 0:
            raise ValueError(f"response_timeout_sec must be > 0, got {self.response_timeout_sec}")
        if self.max_retries < 0:
            raise ValueError(f"max_retries must be >= 0, got {self.max_retries}")
        object.__setattr__(self, "opponent_url", normalise(self.opponent_url))

    @property
    def worst_case_seconds(self) -> float:
        attempts = self.max_retries + 1
        return attempts * self.response_timeout_sec + self.max_retries * self.retry_backoff_sec

    @classmethod
    def from_config(
        cls, network: dict[str, Any], environ: Mapping[str, str] | None = None
    ) -> "ClientSettings":
        source = os.environ if environ is None else environ
        override = source.get(OPPONENT_URL_ENV, "").strip()
        if not override and "opponent_url" not in network:
            raise ValueError(
                f"private config [network] must define opponent_url, or set {OPPONENT_URL_ENV}"
            )
        return cls(opponent_url=override or str(network["opponent_url"]))
