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


class _AcknowledgementMixin1:
    def __post_init__(self) -> None:
        if self.sender not in ROLES:
            raise CeremonyError(f"sender must be one of {sorted(ROLES)}, got {self.sender!r}")
        if self.step < 0:
            raise CeremonyError(f"step must be >= 0, got {self.step}")
        if not DIGEST.match(self.acknowledges):
            raise CeremonyError(
                f"acknowledges must be 64 lowercase hex characters, got {self.acknowledges!r}"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "sender": self.sender,
            "acknowledges": self.acknowledges,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: object) -> "Acknowledgement":
        """Parse an inbound acknowledgement.

        Raises:
            CeremonyError: on anything we would not want to act on.
        """
        try:
            body = require_mapping(data, "acknowledgement")
            return cls(
                step=require_int(body, "step", minimum=0, maximum=10_000),
                sender=require_str(body, "sender"),
                acknowledges=require_str(body, "acknowledges"),
                timestamp=require_str(body, "timestamp"),
            )
        except InvalidPayloadError as exc:
            raise CeremonyError(str(exc)) from exc


def _install(namespace: dict[str, object]) -> None:
    globals().update(namespace)
