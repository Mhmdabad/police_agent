# mypy: ignore-errors
# ruff: noqa
from __future__ import annotations
import queue
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from ..domain.board import BoardState
from ..domain.lock import ScentAgreement, ScentLock, disputes, propose
from ..domain.outcome import TechnicalLoss
from ..infra.ceremony import AuditResult, FinalReveal, MatchCeremony, audit_opponent
from ..infra.handshake import (
    AddressBook,
    Greeting,
    HandshakeError,
    Peering,
    check,
    record,
)
from ..infra.inboxes import DIGEST_KEY, SCENT_DIGEST_KEY, SCENT_KEY, SERIES_KEY, PeerInboxes
from ..infra.mcp_client import OpponentClient, OpponentUnreachableError
from ..shared.config import config_sha256, digests_agree
PROTOCOL_VERSION = "1.0"
GREETING_TIMEOUT_SEC = 30.0
CONFIG_TIMEOUT_SEC = 30.0
SCENT_TIMEOUT_SEC = 30.0
class _OrchestratorMixin1:
    def __post_init__(self) -> None:
        self.client.on_attempt = lambda tool: self.beat(f"attempt:{tool}")
    def beat(self, what: str) -> None:
        self.heartbeats.append(what)
        self.on_event(what)
    def handle_inbound(self, tool: str, payload: object) -> dict[str, Any]:
        self.beat(f"inbound:{tool}")
        handler = {
            "negotiate": self.inboxes.negotiate,
            "receive_turn": self.inboxes.receive_turn,
            "submit_audit": self.inboxes.submit_audit,
            "receive_control": self.inboxes.receive_control,
        }.get(tool)
        if handler is None:
            return {"ok": False, "detail": f"unknown tool {tool!r}"}
        return handler(payload)
    def call_opponent(self, tool: str, payload: dict[str, object]) -> dict[str, Any]:
        self.beat(f"outbound:{tool}")
        try:
            return self.client.call(tool, dict(payload))
        except OpponentUnreachableError as exc:
            raise MatchAborted(TechnicalLoss.TIMEOUT, str(exc)) from exc
    def greeting(self, public_url: str, group_id: str) -> Greeting:
        return Greeting(
            role=self.role,
            group_id=group_id,
            public_url=public_url,
            protocol_version=PROTOCOL_VERSION,
        )
    def announce(self, ours: Greeting) -> dict[str, Any]:
        self.beat("announce")
        return self.call_opponent("negotiate", {"message": {"greeting": ours.to_dict()}})
    def latest_agreement(self, timeout: float) -> dict[str, Any]:
        message = self.next_agreement(timeout)
        while True:
            try:
                message = self.inboxes.agreements.get_nowait()
            except queue.Empty:
                return message
    def next_agreement(self, timeout: float) -> dict[str, Any]:
        try:
            return self.inboxes.agreements.get(timeout=timeout)
        except queue.Empty:
            raise MatchAborted(
                TechnicalLoss.TIMEOUT, f"no greeting from the opponent within {timeout}s"
            ) from None
def _install(namespace: dict[str, object]) -> None:
    globals().update(namespace)
