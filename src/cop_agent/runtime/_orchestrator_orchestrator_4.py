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


class _OrchestratorMixin4:
    def audit(
        self,
        match: MatchCeremony,
        disclosed: FinalReveal,
        sealed_states: dict[int, BoardState],
    ) -> AuditResult:
        self.beat("audit")
        result = audit_opponent(match, disclosed, sealed_states)
        if not result.clean:
            raise MatchAborted(TechnicalLoss.FORGERY, str(result))
        return result

    def agree_config(
        self,
        config: dict[str, Any],
        game_uid: str = "",
        timeout: float = CONFIG_TIMEOUT_SEC,
    ) -> str:
        ours = config_sha256(config)
        self.beat("negotiate_config")
        message: dict[str, object] = {DIGEST_KEY: ours}
        if game_uid:
            message[SERIES_KEY] = game_uid
        reply = self.call_opponent("negotiate", {"message": message})
        if not reply.get("ok", False):
            raise MatchAborted(TechnicalLoss.ILLEGAL_ACTION, str(reply.get("detail", "")))
        self.accept_config_digest(ours, game_uid, timeout)
        return ours

    def accept_config_digest(self, ours: str, game_uid: str, timeout: float) -> str:
        self.beat("await_config")
        deadline = time.monotonic() + timeout
        agreed: str | None = None
        while agreed is None:
            agreed = self.check_digest(self.wait_for_digest(deadline, timeout), ours, game_uid)
        while True:
            try:
                queued = self.inboxes.digests.get_nowait()
            except queue.Empty:
                return agreed
            self.check_digest(queued, ours, game_uid)


def _install(namespace: dict[str, object]) -> None:
    globals().update(namespace)
