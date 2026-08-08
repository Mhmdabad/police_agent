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


class _OrchestratorMixin3:
    def rehandshake(
        self,
        current: Peering,
        ours: Greeting,
        sub_game: int,
        directory: Path,
        game_id: str,
        timeout: float = GREETING_TIMEOUT_SEC,
    ) -> Peering:
        announced = self.try_announce(ours)
        later = self.accept_rotation(current, ours, sub_game, timeout)
        self.adopt(later.theirs)
        if not announced:
            self.announce(ours)
        for role, (was, now) in sorted(current.relocations(later).items()):
            self.beat(f"agreed-move:{role}:{was}->{now}")
        record(directory, game_id, AddressBook.peered(later))
        return later

    def accept_rotation(
        self, current: Peering, ours: Greeting, sub_game: int, timeout: float
    ) -> Peering:
        self.beat("accept_rotation")
        later = self.rotation(current, ours, self.next_agreement(timeout), sub_game)
        while True:
            try:
                queued = self.inboxes.agreements.get_nowait()
            except queue.Empty:
                return later
            later = self.rotation(current, ours, queued, sub_game)

    def rotation(
        self, current: Peering, ours: Greeting, message: dict[str, Any], sub_game: int
    ) -> Peering:
        try:
            return current.rotate(ours, Greeting.from_dict(message.get("greeting")), sub_game)
        except HandshakeError as exc:
            raise MatchAborted(TechnicalLoss.ILLEGAL_ACTION, str(exc)) from exc


def _install(namespace: dict[str, object]) -> None:
    globals().update(namespace)
