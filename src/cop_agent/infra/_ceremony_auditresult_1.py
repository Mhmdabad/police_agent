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


class _AuditResultMixin1:
    @property
    def clean(self) -> bool:
        return self.verdict is Verdict.CLEAN

    def __str__(self) -> str:
        if self.clean:
            return f"{self.checked} steps re-derived, all matching"
        return f"{self.checked} steps re-derived, {len(self.failures)} failed: " + "; ".join(
            self.failures
        )


def _install(namespace: dict[str, object]) -> None:
    globals().update(namespace)
