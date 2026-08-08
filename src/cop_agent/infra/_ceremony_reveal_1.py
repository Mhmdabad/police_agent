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


class _RevealMixin1:
    def __post_init__(self) -> None:
        if self.sender not in ROLES:
            raise CeremonyError(f"sender must be one of {sorted(ROLES)}, got {self.sender!r}")
        if self.step < 0:
            raise CeremonyError(f"step must be >= 0, got {self.step}")
        if self.intent not in INTENTS:
            raise CeremonyError(f"intent must be one of {sorted(INTENTS)}, got {self.intent!r}")
        if not self.game_uid:
            raise CeremonyError("game_uid must not be empty")
        if not 1 <= self.sub_game <= 6:
            raise CeremonyError(f"sub_game must be between 1 and 6, got {self.sub_game}")

    def to_dict(self) -> dict[str, Any]:
        """The wire form. :data:`REVEAL_FIELDS`, and no nonce in it."""
        return {
            "step": self.step,
            "sender": self.sender,
            "move": self.move,
            "intent": self.intent,
            "hint": self.hint,
            "barrier_placed": self.barrier_placed,
            "scent": self.scent,
            "timestamp": self.timestamp,
            "game_uid": self.game_uid,
            "sub_game": self.sub_game,
        }

    @classmethod
    def from_dict(cls, data: object, *, hint_max_words: int = 15) -> "Reveal":
        """Parse an inbound reveal.

        A nonce arriving here is **refused**, not ignored. Every other stray
        field in this module is dropped quietly, because reading less is always
        safe — but a nonce is the one value whose early arrival means the
        opponent has misunderstood the ceremony, and continuing would let us
        hold a secret we are not supposed to have until the audit. Better to
        stop than to be in possession of it.

        Raises:
            CeremonyError: on anything malformed, or on a nonce.
        """
        try:
            body = require_mapping(data, "reveal")
            if "nonce" in body:
                raise CeremonyError(
                    f"reveal for step {body.get('step')} carries a nonce; it is withheld until "
                    "the final audit, and one early nonce weakens every other commitment"
                )
            return cls(
                step=require_int(body, "step", minimum=0, maximum=10_000),
                sender=require_str(body, "sender"),
                move=require_str(body, "move"),
                intent=require_str(body, "intent"),
                hint=require_hint(body, max_words=hint_max_words),
                timestamp=require_str(body, "timestamp"),
                game_uid=require_str(body, "game_uid"),
                sub_game=require_int(body, "sub_game", minimum=1, maximum=6),
                barrier_placed=optional_cell(body, "barrier_placed"),
                scent=optional_scent(body, "scent"),
            )
        except InvalidPayloadError as exc:
            raise CeremonyError(str(exc)) from exc


def _install(namespace: dict[str, object]) -> None:
    globals().update(namespace)
