# mypy: ignore-errors
# ruff: noqa
from __future__ import annotations

import hashlib

import queue

from collections.abc import Callable

from dataclasses import dataclass, field

from typing import Any, Protocol

from ..shared.config import canonical_bytes

from .ceremony import CeremonyError, Reveal

from .protocol import AuditPayload, ControlMessage, TurnMessage

from .validation import (
    InvalidPayloadError,
    optional_scent,
    require_digest,
    require_mapping,
    require_str,
)

DIGEST_KEY = "config_sha256"

SERIES_KEY = "game_uid"

SCENT_KEY = "scent_lock"

SCENT_DIGEST_KEY = "scent_sha256"

RETRY_KEY = "retry"

ACK: dict[str, Any] = {"ok": True}

TOOL_NAMES: tuple[str, ...] = ("negotiate", "receive_turn", "submit_audit", "receive_control")


class _PeerInboxesMixin1:
    def bind(self, game_uid: str, sub_game: int) -> None:
        """Open this mailbox for exactly one sub-game of exactly one series.

        Called where the *next* thing we do is tell the opponent we are ready —
        the agreement that opens the series, and the re-greeting that opens each
        later sub-game. Both are messages they wait for before sending anything
        of their own, so binding first is what makes the retryable refusal below
        a safety net rather than the mechanism: an honest peer's opening packet
        arrives at a door that is already open.

        **The series is widened before the sub-game is narrowed, deliberately.**
        These are two separate stores and the door is read on the server thread,
        so a message can land between them. Taking the series first means the
        worst it can see is a door still pointing at the sub-game we just left,
        which *defers* the sender; taking the sub-game first would briefly point
        at a series we are not in, which refuses it for good.
        """
        self.game_uid = game_uid
        self.sub_game = sub_game

    def _refuse(self, what: str, exc: ValueError) -> dict[str, Any]:
        """Record a refusal without raising across the wire.

        Kept rather than discarded: a match that ends in a dispute needs to
        show what arrived and why it was not acted on.
        """
        self.rejected.append(f"{what}: {exc}")
        return {"ok": False, "detail": str(exc)}

    def _reject(self, what: str, detail: str) -> dict[str, Any]:
        """Refuse something well-formed that we will not act on."""
        self.rejected.append(f"{what}: {detail}")
        return {"ok": False, "detail": detail}

    def _closed(self, what: str, game_uid: str, sub_game: int) -> tuple[str, bool] | None:
        """Why a binding may not enter a queue, and whether asking again would help.

        ``None`` when the message names **exactly** the sub-game of exactly the
        series this mailbox is bound to; otherwise the reason, paired with
        whether the sender should try again.

        **Exactly, and nothing else.** The looser rule this replaces admitted
        anything that was not provably behind us, which sounds conservative and
        is the opposite: "not behind us" is also true of every packet that
        arrives before we have bound anything at all, so an unbound mailbox
        queued whatever it was sent and wrote its duplicate ledger from it. A
        forged commitment pushed in that window took the head of the queue and
        stranded the legitimate one behind it.

        **Two kinds of no, because there are two kinds of reason.** A binding we
        cannot yet judge — no series agreed, or a sub-game this series has not
        opened — is a statement about *us*, so the sender is asked to come back
        and :data:`RETRY_KEY` says so. A binding we can judge and have refused —
        another series, or a sub-game we are already past — is a statement about
        *the message*, and repeating it changes nothing.

        The deferral is what makes the strict rule safe. Demanding equality with
        no way to say "not yet" is what broke the series before: both peers
        advance this binding on their own thread, so the one that crossed a
        boundary first had its opening commitment refused at a door still set to
        the sub-game we had both just left, and ``receive_turn`` is
        fire-and-forget, so that single silent refusal cost the rest of the
        series. :meth:`bind` orders the two sides so it should not arise at all;
        this is what happens when it does anyway.
        """
        if not self.game_uid:
            return (
                f"{what} arrived before this mailbox was bound to a series; nothing is "
                "queued against a binding we have not agreed yet",
                True,
            )
        if game_uid != self.game_uid:
            return (
                f"{what} is bound to series {game_uid!r}, and we are playing {self.game_uid!r}",
                False,
            )
        if sub_game > self.sub_game:
            return (
                f"{what} is bound to sub-game {sub_game}, which this series has not opened "
                f"yet at sub-game {self.sub_game}",
                True,
            )
        if sub_game < self.sub_game:
            return (
                f"{what} is bound to sub-game {sub_game}, which this series is already "
                f"past at sub-game {self.sub_game}",
                False,
            )
        return None

    def _shut(self, what: str, closed: tuple[str, bool]) -> dict[str, Any]:
        """Answer a closed door, saying whether coming back would help."""
        detail, retry = closed
        if not retry:
            return self._reject(what, detail)
        self.deferred.append(f"{what}: {detail}")
        return {"ok": False, RETRY_KEY: True, "detail": detail}


def _install(namespace: dict[str, object]) -> None:
    globals().update(namespace)
