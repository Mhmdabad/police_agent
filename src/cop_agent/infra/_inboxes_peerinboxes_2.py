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
class _PeerInboxesMixin2:
    def negotiate(self, message: object) -> dict[str, Any]:
        try:
            body = require_mapping(message, "agreement")
            if SCENT_KEY in body:
                self.scent_locks.put(self._scent_lock(body))
            elif DIGEST_KEY in body:
                self.digests.put(self._digest(body))
            else:
                self.agreements.put(body)
        except InvalidPayloadError as exc:
            return self._refuse("negotiate", exc)
        return ACK
    def _scent_lock(self, body: dict[str, Any]) -> dict[str, Any]:
        offer = require_mapping(body[SCENT_KEY], SCENT_KEY)
        model = require_mapping(offer.get("scent_model"), f"{SCENT_KEY}.scent_model")
        optional_scent(model, "emission")
        return {
            **body,
            SCENT_KEY: offer,
            SCENT_DIGEST_KEY: require_digest(body, SCENT_DIGEST_KEY),
            SERIES_KEY: require_str(body, SERIES_KEY),
        }
    def _digest(self, body: dict[str, Any]) -> dict[str, Any]:
        filed = {**body, DIGEST_KEY: require_digest(body, DIGEST_KEY)}
        if SERIES_KEY in body:
            filed[SERIES_KEY] = require_str(body, SERIES_KEY)
        return filed
    def receive_turn(self, message: object) -> dict[str, Any]:
        try:
            turn = TurnMessage.from_dict(message)
        except InvalidPayloadError as exc:
            return self._refuse("receive_turn", exc)
        closed = self._closed("turn", turn.game_uid, turn.sub_game)
        if closed is not None:
            return self._shut("receive_turn", closed)
        key = (turn.sender, turn.step, turn.game_uid, turn.sub_game)
        digest = fingerprint(turn)
        taken = self.accepted_turns.get(key)
        if taken == digest:
            self.duplicates.append(f"receive_turn: {turn.sender} step {turn.step} re-sent")
            return ACK
        if taken is not None:
            return self._reject(
                "receive_turn",
                f"{turn.sender} already played step {turn.step} with a different message; "
                "a retry may re-send an action, never replace one",
            )
        self.accepted_turns[key] = digest
        self.turns.put(turn)
        return ACK
def _install(namespace: dict[str, object]) -> None:
    globals().update(namespace)
