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


class _PeerInboxesMixin3:
    def submit_audit(self, payload: object) -> dict[str, Any]:
        """Receive the opponent's end-of-game reveal: records and nonces.

        **Two bindings are compared.** The envelope goes through
        :meth:`_closed`, so nothing is opened against a series or a sub-game
        that is not the one we are playing. Each record inside is then checked
        against *the envelope it arrived in* rather than against our position
        again — the sender wrote both, so they must agree, and a reveal
        re-wrapped in a fresher audit to replay an earlier sub-game is exactly
        the disagreement that exposes.
        """
        try:
            audit = AuditPayload.from_dict(payload)
            closed = self._closed("audit payload", audit.game_uid, audit.sub_game)
            if closed is not None:
                return self._shut("submit_audit", closed)
            fresh: list[dict[str, Any]] = []
            pending: dict[tuple[str, int, str, int], str] = {}
            for record in audit.records:
                if "move" not in record:
                    fresh.append(record)
                    continue
                opened = Reveal.from_dict(record, hint_max_words=self.hint_max_words)
                if opened.game_uid != audit.game_uid or opened.sub_game != audit.sub_game:
                    return self._reject(
                        "submit_audit",
                        f"reveal is bound to {opened.game_uid!r} sub-game {opened.sub_game} "
                        f"but travelled in an audit for {audit.game_uid!r} sub-game "
                        f"{audit.sub_game}",
                    )
                key = (opened.sender, opened.step, opened.game_uid, opened.sub_game)
                if key not in self.accepted_turns:
                    return self._reject(
                        "submit_audit",
                        f"{opened.sender} revealed step {opened.step} of {opened.game_uid!r} "
                        f"sub-game {opened.sub_game} without a current phase-one commitment",
                    )
                digest = hashlib.sha256(canonical_bytes(opened.to_dict())).hexdigest()
                taken = pending.get(key, self.accepted_reveals.get(key))
                if taken == digest:
                    self.duplicates.append(
                        f"submit_audit: {opened.sender} step {opened.step} re-sent"
                    )
                    continue
                if taken is not None:
                    return self._reject(
                        "submit_audit",
                        f"{opened.sender} already revealed step {opened.step} differently",
                    )
                pending[key] = digest
                fresh.append(record)
            self.accepted_reveals.update(pending)
            if fresh or not audit.records:
                self.audits.put(
                    AuditPayload(
                        audit.sender,
                        fresh,
                        audit.result_claim,
                        audit.game_uid,
                        audit.sub_game,
                    )
                )
        except (InvalidPayloadError, CeremonyError) as exc:
            return self._refuse("submit_audit", exc)
        return ACK

    def receive_control(self, message: object) -> dict[str, Any]:
        """Receive a control signal: enable, status, restart or quit."""
        try:
            self.controls.put(ControlMessage.from_dict(message))
        except InvalidPayloadError as exc:
            return self._refuse("receive_control", exc)
        return ACK


def _install(namespace: dict[str, object]) -> None:
    globals().update(namespace)
