# mypy: ignore-errors
# ruff: noqa
from __future__ import annotations

import queue

import time

from collections.abc import Callable

from dataclasses import dataclass, field

from typing import Any

from ..infra.ceremony import Acknowledgement, CeremonyError, Commitment, FinalReveal, Reveal

from ..infra.inboxes import PeerInboxes

from ..infra.mcp_client import OpponentClient

from ..infra.protocol import AuditPayload, TurnMessage

Record = dict[str, Any]

Wanted = Callable[[Record], bool]

UNDECIDED = "in_progress"


class _McpPeerMixin2:
    def _await_reveal_record(self, step: int) -> Record:
        """Return the one reveal for ``step`` after classifying every sibling."""
        deadline = time.monotonic() + self.timeout
        while True:
            current: list[Record] = []
            kept: list[Record] = []
            for record in self._held:
                record_step = record.get("step")
                if "move" not in record or not isinstance(record_step, int) or record_step > step:
                    kept.append(record)
                elif record_step < step:
                    self.quarantined.append(record)
                else:
                    current.append(record)
            self._held = kept
            if current:
                canonical = current[0]
                if any(record != canonical for record in current[1:]):
                    raise CeremonyError(f"conflicting reveals for step {step}")
                return canonical
            self._hold_payload(deadline)

    def _hold_payload(self, deadline: float) -> None:
        """Take one audit payload, holding what is ours and quarantining what is not.

        Both bindings are checked, and a failure of either sets the record aside
        rather than ending the wait. The envelope can only be foreign if it
        reached a mailbox that was not yet bound; a record can only be foreign
        if the sender wrapped an old reveal in a current envelope, which is the
        replay the inner binding exists to catch. Neither is a reason to stop
        waiting for the reveal that *is* ours.
        """
        payload = self._drain(self.inboxes.audits, None, "audit record", deadline)
        ours = payload.game_uid == self.game_uid and payload.sub_game == self.sub_game
        for entry in payload.records:
            record = dict(entry)
            if ours and not self._foreign(record):
                self._held.append(record)
            else:
                self.quarantined.append(record)

    def _foreign(self, record: Record) -> bool:
        """Whether a record names a binding that is not the one we are playing.

        A record that names none — a final reveal carries nonces and no
        sub-game — is bound by the envelope it travelled in, which has already
        been checked, so it is ours by default rather than foreign by omission.
        """
        return bool(
            record.get("game_uid", self.game_uid) != self.game_uid
            or record.get("sub_game", self.sub_game) != self.sub_game
        )

    def _await_record(self, wanted: Wanted) -> Record:
        """Find a record we are waiting for, keeping the ones we are not.

        Reveals and final reveals share one queue, and they do not arrive in
        the order any single caller wants — a final reveal can land while a
        step's reveal is still outstanding. Records that do not match are held
        rather than dropped, because a discarded message is a deadlock nobody
        can diagnose.
        """
        for kept in list(self._held):
            if wanted(kept):
                self._held.remove(kept)
                return kept
        deadline = time.monotonic() + self.timeout
        while True:
            self._hold_payload(deadline)
            for kept in list(self._held):
                if wanted(kept):
                    self._held.remove(kept)
                    return kept

    def _drain(
        self,
        inbox: "queue.Queue[Any]",
        step: int | None,
        what: str,
        deadline: float | None = None,
    ) -> Any:  # noqa: ANN401
        """Take the next message off an inbox, or say who stopped talking.

        Returns whatever that inbox holds — a ``TurnMessage`` or an
        ``AuditPayload``. Typed loosely because the queues are, and narrowing
        it here would mean two near-identical copies of the timeout message.

        ``deadline`` is what a caller that may have to take several messages
        waits against, so setting a foreign one aside costs no extra patience:
        the whole search shares the one allowance the caller was given.
        """
        remaining = self.timeout if deadline is None else max(deadline - time.monotonic(), 0.0)
        try:
            return inbox.get(timeout=remaining)
        except queue.Empty as exc:
            where = "" if step is None else f" for step {step}"
            raise PeerTimeout(
                f"waited {self.timeout:g}s for the {self.opponent}'s {what}{where} and it "
                "never came; a peer that stops answering is a technical loss, which "
                "scores zero for both sides"
            ) from exc


def _install(namespace: dict[str, object]) -> None:
    globals().update(namespace)
