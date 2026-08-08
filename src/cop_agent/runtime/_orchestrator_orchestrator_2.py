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


class _OrchestratorMixin2:
    def try_announce(self, ours: Greeting) -> bool:
        """Announce, tolerating an outbound path that no longer exists.

        Only for the re-handshake, where the address we hold may be the very
        thing that has gone stale. Everywhere else a failed call is a technical
        loss and should stay one — a helper that quietly swallows unreachable
        opponents is the fastest way to turn a lost match into a silent one.

        Returns:
            Whether the announcement actually landed.
        """
        try:
            self.announce(ours)
        except MatchAborted:
            self.beat("announce-failed")
            return False
        return True

    def accept_greeting(self, ours: Greeting, timeout: float = GREETING_TIMEOUT_SEC) -> Greeting:
        """Take the opponent's greeting off the queue and decide if we can play.

        Fire-and-forget, like every other inbound message: their greeting is
        pushed into *our* server and drains from :attr:`PeerInboxes.agreements`
        rather than arriving as the return value of our own call.

        The checks live in :func:`~..infra.handshake.check`, which is the only
        validator of a greeting. Re-checking the role and version here — as an
        earlier ``check_handshake`` did — meant two validators that could
        disagree, and the pair that disagrees is always the pair that matters.

        Raises:
            MatchAborted: ``TIMEOUT`` if no greeting arrives inside the window,
                ``ILLEGAL_ACTION`` if the one that does cannot be played
                against. A missed deadline is a failure, not a reason to wait.
        """
        self.beat("accept_greeting")
        message = self.latest_agreement(timeout)
        try:
            theirs = Greeting.from_dict(message.get("greeting"))
            check(ours, theirs)
        except HandshakeError as exc:
            raise MatchAborted(TechnicalLoss.ILLEGAL_ACTION, str(exc)) from exc
        return theirs

    def open_series(
        self,
        ours: Greeting,
        directory: Path,
        game_id: str,
        timeout: float = GREETING_TIMEOUT_SEC,
    ) -> Peering:
        """Trade addresses and write both into the pre-game declaration.

        Announcing first is deliberate. Waiting for the opponent before saying
        anything is a handshake where two polite peers wait for each other
        forever — the deadlock the state machine exists to make impossible.

        Returns the addresses in force for sub-game 1. Later sub-games go
        through :meth:`rehandshake`, which is the same exchange with the
        additional rule that only the address may have moved.
        """
        self.announce(ours)
        peering = Peering(ours, self.accept_greeting(ours, timeout), sub_game=1)
        self.adopt(peering.theirs)
        record(directory, game_id, AddressBook.peered(peering))
        return peering

    def adopt(self, theirs: Greeting) -> None:
        """Point the client at the address the opponent actually announced.

        ``opponent_url`` in the private config is a **bootstrap** address: it
        is how we reach them the first time, and it is whatever we were told
        out of band. Their greeting is the authoritative statement of where
        they are, and it is the value the declaration records — so calls that
        went somewhere else would contradict the file we both signed.

        Only ever called from an accepted greeting. Following a redirect the
        transport happened to return would be a different thing entirely.
        """
        was = self.client.repoint(theirs.public_url)
        if was != theirs.public_url:
            self.beat(f"relocated:{theirs.role}:{was}->{theirs.public_url}")


def _install(namespace: dict[str, object]) -> None:
    globals().update(namespace)
