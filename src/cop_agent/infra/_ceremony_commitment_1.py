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


class _CommitmentMixin1:
    def __post_init__(self) -> None:
        if self.sender not in ROLES:
            raise CeremonyError(f"sender must be one of {sorted(ROLES)}, got {self.sender!r}")
        if self.step < 0:
            raise CeremonyError(f"step must be >= 0, got {self.step}")
        if not DIGEST.match(self.commit):
            raise CeremonyError(
                f"commit must be 64 lowercase hex characters, got {self.commit!r}; "
                "a malformed digest would surface later as a forgery verdict "
                "against an opponent whose only mistake was formatting"
            )
        if not self.game_uid:
            raise CeremonyError("game_uid must not be empty")
        if not 1 <= self.sub_game <= 6:
            raise CeremonyError(f"sub_game must be between 1 and 6, got {self.sub_game}")

    def to_dict(self) -> dict[str, Any]:
        """The wire form. Exactly :data:`COMMIT_FIELDS` and never more."""
        return {
            "step": self.step,
            "sender": self.sender,
            "commit": self.commit,
            "timestamp": self.timestamp,
            "game_uid": self.game_uid,
            "sub_game": self.sub_game,
        }

    @classmethod
    def from_dict(cls, data: object) -> "Commitment":
        """Parse an inbound commitment, ignoring anything extra.

        Extra keys are dropped rather than refused. We cannot stop an opponent
        putting their move in the message, and refusing would let them end our
        match by sending one — but we can decline to *read* it, so nothing
        downstream can act on information phase 1 was not supposed to carry.

        Raises:
            CeremonyError: on anything we would not want to file.
        """
        try:
            body = require_mapping(data, "commitment")
            return cls(
                step=require_int(body, "step", minimum=0, maximum=10_000),
                sender=require_str(body, "sender"),
                commit=require_str(body, "commit"),
                timestamp=require_str(body, "timestamp"),
                game_uid=require_str(body, "game_uid"),
                sub_game=require_int(body, "sub_game", minimum=1, maximum=6),
            )
        except InvalidPayloadError as exc:
            raise CeremonyError(str(exc)) from exc


def _install(namespace: dict[str, object]) -> None:
    globals().update(namespace)
