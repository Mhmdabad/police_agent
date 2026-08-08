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


class _StepCeremonyMixin2:
    def reveal(self, opened: Reveal) -> Reveal:
        """Disclose our action and hint, once and only once both sides are locked.

        Raises:
            CeremonyError: if the lock is incomplete, or on a second reveal.
                Revealing early is not an efficiency — it hands the opponent
                our move while theirs is still free to change, which is the one
                thing the acknowledgement was for.
        """
        if not self.locked:
            raise CeremonyError(
                f"cannot reveal step {self.step} before both sides are locked ({self.pending()}); "
                "revealing early hands over our move while theirs can still change"
            )
        if self.revealed_ours is not None:
            raise CeremonyError(f"step {self.step} is already revealed; a reveal is not revisable")
        self._check_belongs(opened.step, opened.sender, expected_role=self.role, what="reveal")
        assert self.ours is not None
        self._check_binding(opened.game_uid, opened.sub_game, self.ours, "reveal")
        self.revealed_ours = opened
        return opened

    def receive_reveal(self, opened: Reveal) -> Reveal:
        """File the opponent's disclosure. **It cannot be checked yet.**

        The digest cannot be recomputed without their nonce, so this is
        believed on the strength of the lock and verified only at the final
        audit. Storing it is therefore the whole job: a reveal we did not keep
        is a step the audit cannot re-derive, and an audit that cannot
        re-derive a step proves nothing about it either way.

        Raises:
            CeremonyError: if they have not committed, if we are not locked, or
                on a second reveal for the step.
        """
        if not self.locked:
            raise CeremonyError(
                f"the opponent revealed step {self.step} before both sides were locked "
                f"({self.pending()}); accepting it would reward revealing early"
            )
        if self.revealed_theirs is not None:
            raise CeremonyError(
                f"the opponent already revealed step {self.step}; "
                "a second disclosure would replace an action we have acted on"
            )
        self._check_belongs(opened.step, opened.sender, expected_role=self.opponent, what="reveal")
        assert self.theirs is not None
        self._check_binding(opened.game_uid, opened.sub_game, self.theirs, "reveal")
        self.revealed_theirs = opened
        return opened

    def pending(self) -> str:
        """Which parts of the lock are still missing. For the error, and the log."""
        missing = [
            name
            for name, part in (
                ("our commitment", self.ours),
                ("their commitment", self.theirs),
                ("our acknowledgement", self.ack_sent),
                ("their acknowledgement", self.ack_received),
            )
            if part is None
        ]
        return "missing " + ", ".join(missing) if missing else "locked"

    def _check_belongs(self, step: int, sender: str, expected_role: str, what: str) -> None:
        if step != self.step:
            raise CeremonyError(f"{what} is for step {step}, this ceremony is step {self.step}")
        if sender != expected_role:
            raise CeremonyError(f"{what} is from {sender!r}, expected {expected_role!r}")

    @staticmethod
    def _check_binding(game_uid: str, sub_game: int, locked: Commitment, what: str) -> None:
        if game_uid != locked.game_uid or sub_game != locked.sub_game:
            raise CeremonyError(
                f"{what} binding {game_uid!r}/{sub_game} does not match locked commitment "
                f"{locked.game_uid!r}/{locked.sub_game}"
            )


def _install(namespace: dict[str, object]) -> None:
    globals().update(namespace)
