# mypy: ignore-errors
# ruff: noqa
from __future__ import annotations

import re

import secrets

from dataclasses import dataclass, field

from enum import Enum

from typing import Any

from ..domain.actions import ROLES

from ..domain.bluff import INTENTS

from ..domain.board import BoardState

from ..domain.crypto import NONCE_BYTES, commit_of, step_record

from .validation import (
    InvalidPayloadError,
    optional_cell,
    optional_scent,
    require_hint,
    require_int,
    require_mapping,
    require_str,
)

DIGEST = re.compile(r"^[0-9a-f]{64}$")

NONCE_LENGTH = NONCE_BYTES * 2

NONCE = re.compile(rf"^[0-9a-f]{{{NONCE_LENGTH}}}$")

COMMIT_FIELDS = ("step", "sender", "commit", "timestamp", "game_uid", "sub_game")

ACK_FIELDS = ("step", "sender", "acknowledges", "timestamp")

REVEAL_FIELDS = (
    "step",
    "sender",
    "move",
    "intent",
    "hint",
    "barrier_placed",
    "scent",
    "timestamp",
    "game_uid",
    "sub_game",
)


class _MatchCeremonyMixin1:
    def __post_init__(self) -> None:
        if self.role not in ROLES:
            raise CeremonyError(f"role must be one of {sorted(ROLES)}, got {self.role!r}")

    def at(self, step: int) -> StepCeremony:
        """The ceremony for ``step``, opening one if this is its first message."""
        if step not in self.steps:
            self.steps[step] = StepCeremony(step=step, role=self.role)
        return self.steps[step]

    def finish(self) -> None:
        """Mark the match over. Only after this may nonces be disclosed."""
        self.over = True

    def final_reveal(self, timestamp: str) -> FinalReveal:
        """Disclose every nonce of the match, at the end, in one message.

        Raises:
            CeremonyError: while the match is still running, or if any step
                cannot contribute a nonce. Both refusals protect the same
                thing from opposite sides — an early disclosure reopens
                commitments that still matter, and a partial one leaves a step
                nobody can re-derive, which is precisely the step a cheat would
                omit.
        """
        if not self.over:
            raise CeremonyError(
                "cannot disclose nonces while the match is running; every step uses the "
                "same construction, so one released early narrows all the others"
            )
        missing = sorted(step for step, one in self.steps.items() if one.our_nonce is None)
        if missing:
            raise CeremonyError(
                f"no nonce recorded for step(s) {missing}; a step nobody can re-derive "
                "proves nothing at audit, which is what makes a partial reveal worse "
                "than a late one"
            )
        return FinalReveal(
            sender=self.role,
            nonces={step: one.our_nonce for step, one in self.steps.items() if one.our_nonce},
            timestamp=timestamp,
        )

    def receive_final_reveal(self, disclosed: FinalReveal) -> FinalReveal:
        """File the opponent's nonces, checking they cover what they committed to.

        Raises:
            CeremonyError: if it comes from the wrong role, or omits a step
                they committed to. Extra steps are tolerated — a nonce for a
                step we have no record of verifies nothing and harms nothing —
                but a **missing** one is the shape of a hidden move.
        """
        if disclosed.sender != self.opponent:
            raise CeremonyError(
                f"final reveal is from {disclosed.sender!r}, expected {self.opponent!r}"
            )
        owed = {step for step, one in self.steps.items() if one.theirs is not None}
        absent = sorted(owed - set(disclosed.nonces))
        if absent:
            raise CeremonyError(
                f"their final reveal omits step(s) {absent}, which they committed to; "
                "an unopenable commitment is indistinguishable from a hidden move"
            )
        return disclosed

    @property
    def opponent(self) -> str:
        """The role that is not ours."""
        return next(role for role in sorted(ROLES) if role != self.role)


def _install(namespace: dict[str, object]) -> None:
    globals().update(namespace)
