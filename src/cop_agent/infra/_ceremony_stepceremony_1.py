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


class _StepCeremonyMixin1:
    def __post_init__(self) -> None:
        if self.role not in ROLES:
            raise CeremonyError(f"role must be one of {sorted(ROLES)}, got {self.role!r}")

    def commit(self, ours: Commitment, nonce: str) -> Commitment:
        if self.ours is not None:
            raise CeremonyError(
                f"step {self.step} is already committed; a commitment is not revisable"
            )
        if not NONCE.match(nonce):
            raise CeremonyError(f"nonce is not {NONCE_LENGTH} hex characters: {nonce!r}")
        self._check_belongs(ours.step, ours.sender, expected_role=self.role, what="commitment")
        self.ours = ours
        self.our_nonce = nonce
        return ours

    def receive(self, theirs: Commitment) -> Commitment:
        if self.theirs is not None:
            raise CeremonyError(
                f"the opponent already committed to step {self.step}; "
                "a second commitment would replace a move that is already locked"
            )
        self._check_belongs(
            theirs.step, theirs.sender, expected_role=self.opponent, what="commitment"
        )
        if self.ours is not None:
            self._check_binding(theirs.game_uid, theirs.sub_game, self.ours, "commitment")
        self.theirs = theirs
        return theirs

    def acknowledge(self, timestamp: str) -> Acknowledgement:
        if self.theirs is None:
            raise CeremonyError(
                f"nothing to acknowledge at step {self.step}; the opponent has not committed, "
                "and acknowledging would tell them to reveal into a step we cannot check"
            )
        self.ack_sent = Acknowledgement(
            step=self.step,
            sender=self.role,
            acknowledges=self.theirs.commit,
            timestamp=timestamp,
        )
        return self.ack_sent

    def receive_ack(self, ack: Acknowledgement) -> Acknowledgement:
        if self.ours is None:
            raise CeremonyError(f"acknowledgement for step {self.step} arrived before we committed")
        self._check_belongs(
            ack.step, ack.sender, expected_role=self.opponent, what="acknowledgement"
        )
        if ack.acknowledges != self.ours.commit:
            raise CeremonyError(
                f"they acknowledged {ack.acknowledges[:16]}… but we committed "
                f"{self.ours.commit[:16]}…; that is a lock on a commitment we never made"
            )
        self.ack_received = ack
        return ack

    @property
    def opponent(self) -> str:
        return next(role for role in sorted(ROLES) if role != self.role)

    @property
    def locked(self) -> bool:
        return all(
            part is not None for part in (self.ours, self.theirs, self.ack_sent, self.ack_received)
        )


def _install(namespace: dict[str, object]) -> None:
    globals().update(namespace)
