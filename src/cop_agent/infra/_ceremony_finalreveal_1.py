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


class _FinalRevealMixin1:
    def __post_init__(self) -> None:
        if self.sender not in ROLES:
            raise CeremonyError(f"sender must be one of {sorted(ROLES)}, got {self.sender!r}")
        for step, value in sorted(self.nonces.items()):
            if step < 0:
                raise CeremonyError(f"step must be >= 0, got {step}")
            if not NONCE.match(value):
                raise CeremonyError(
                    f"nonce for step {step} is not {NONCE_LENGTH} hex characters: {value!r}"
                )

    def to_dict(self) -> dict[str, Any]:
        """The wire form. Step keys become strings, as JSON requires."""
        return {
            "sender": self.sender,
            "nonces": {str(step): value for step, value in sorted(self.nonces.items())},
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: object) -> "FinalReveal":
        """Parse an inbound final reveal.

        Raises:
            CeremonyError: on anything malformed. A step key that is not an
                integer is refused rather than skipped: a nonce we cannot file
                against a step is a nonce that verifies nothing, and silently
                dropping it would turn their formatting error into our
                unverifiable step.
        """
        try:
            body = require_mapping(data, "final reveal")
            raw = body.get("nonces")
            if not isinstance(raw, dict):
                raise CeremonyError(f"'nonces' must be an object, got {type(raw).__name__}")
            nonces: dict[int, str] = {}
            for key, value in raw.items():
                try:
                    step = int(key)
                except (TypeError, ValueError) as exc:
                    raise CeremonyError(f"step key {key!r} is not an integer") from exc
                if not isinstance(value, str):
                    raise CeremonyError(f"nonce for step {step} is not a string")
                nonces[step] = value
            return cls(
                sender=require_str(body, "sender"),
                nonces=nonces,
                timestamp=require_str(body, "timestamp"),
            )
        except InvalidPayloadError as exc:
            raise CeremonyError(str(exc)) from exc


def _install(namespace: dict[str, object]) -> None:
    globals().update(namespace)
