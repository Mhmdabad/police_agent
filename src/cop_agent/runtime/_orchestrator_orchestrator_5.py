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


class _OrchestratorMixin5:
    def wait_for_digest(self, deadline: float, timeout: float) -> dict[str, Any]:
        """The next digest message, or a timeout. Never an unbounded wait.

        Raises:
            MatchAborted: ``TIMEOUT`` once the deadline passes. Silence at this
                gate is a refusal to agree, not a reason to wait longer.
        """
        try:
            return self.inboxes.digests.get(timeout=max(deadline - time.monotonic(), 0.0))
        except queue.Empty:
            raise MatchAborted(
                TechnicalLoss.TIMEOUT,
                f"no config digest from the opponent within {timeout:g}s; an "
                "unanswered agreement is a refusal to agree, and a series played "
                "without one is void either way",
            ) from None

    def check_digest(self, body: dict[str, Any], ours: str, game_uid: str) -> str | None:
        """Their digest from one message, or ``None`` if it is not about this series.

        Compared in constant time through :func:`~..shared.config.digests_agree`,
        against the canonical lowercase form :func:`require_digest` normalises to
        at the door — so this only ever compares two values of the same shape.

        Raises:
            MatchAborted: ``ILLEGAL_ACTION`` if their parameters are not ours.
        """
        theirs = str(body.get(DIGEST_KEY, ""))
        about = str(body.get(SERIES_KEY, ""))
        if game_uid and about and about != game_uid:
            self.beat(f"stale-digest:{about}")
            return None
        if not digests_agree(ours, theirs):
            raise MatchAborted(
                TechnicalLoss.ILLEGAL_ACTION,
                f"the opponent is playing by {theirs} and we are playing by {ours}; "
                "Appendix E rule 11 requires byte-identical configuration on both "
                "sides, and a series played on two sets of physics produces two "
                "logs nobody can reconcile — zero for both teams",
            )
        return theirs

    def agree_scent_model(
        self,
        game_uid: str,
        ours: ScentLock | None = None,
        timeout: float = SCENT_TIMEOUT_SEC,
    ) -> ScentAgreement:
        """Exchange the scent-emission model, refusing to play unless it is shared.

        Appendix E rule 23: the model is locked cryptographically **before** the
        game starts, and a deviation in the decay formula voids the match. The
        lock existed and was never sent — ``domain/lock.py`` had no import site
        in ``src/`` at all — so the two known divergences from the reference
        implementation surfaced as an audit failure halfway through a series
        instead of as a conversation before it opened.

        The offer is built from the **live engine** through
        :func:`~..domain.lock.propose`, never transcribed, so what we hash is
        what we will actually emit. Whatever it says, it says only about the
        published 5x5 worked example: no nonce exists yet, no commitment has
        been made, and the live board is not an input, so nothing about our
        position can travel in it.

        **Speak, then listen**, exactly as :meth:`agree_config` does and for the
        same reason: both peers run this at once and each blocks on a message
        only the other can send.

        Args:
            game_uid: the series this lock is about. Required rather than
                optional — unlike the config digest, this message is our dialect
                and not the reference's, so a peer sending one at all can bind
                it. An empty value is refused by the opponent's own door, which
                is where we would rather learn about it than at their audit.

        Raises:
            MatchAborted: ``ILLEGAL_ACTION`` if their model is not ours or their
                offer was refused, ``TIMEOUT`` if none arrives inside the window.
        """
        ours = ours or propose()
        self.beat("negotiate_scent")
        reply = self.call_opponent("negotiate", {"message": self.scent_offer(ours, game_uid)})
        if not reply.get("ok", False):
            raise MatchAborted(TechnicalLoss.ILLEGAL_ACTION, str(reply.get("detail", "")))
        return self.accept_scent_lock(ours, game_uid, timeout)

    @staticmethod
    def scent_offer(ours: ScentLock, game_uid: str) -> dict[str, object]:
        """The canonical offer: the model, its digest, and the series it binds."""
        return {SCENT_KEY: ours.terms(), SCENT_DIGEST_KEY: ours.digest(), SERIES_KEY: game_uid}


def _install(namespace: dict[str, object]) -> None:
    globals().update(namespace)
