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


class _ToolHostMixin1:
    def tool(self, fn: Callable[..., dict[str, Any]]) -> object: ...


def _install(namespace: dict[str, object]) -> None:
    globals().update(namespace)
