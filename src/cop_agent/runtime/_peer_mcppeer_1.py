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


class _McpPeerMixin1:
    @property
    def opponent(self) -> str:
        return "thief" if self.role == "police" else "police"

    def send_commit(self, commitment: Commitment) -> None:
        """Send our digest, and keep whatever came back as their acknowledgement."""
        turn = TurnMessage(
            step=commitment.step,
            sender=self.role,
            hint="",
            smell_grid={},
            commit=commitment.commit,
            timestamp=commitment.timestamp,
            game_uid=commitment.game_uid,
            sub_game=commitment.sub_game,
        )
        answer = self.client.call("receive_turn", {"message": turn.to_dict()})
        self.acks[commitment.step] = self._read_ack(commitment, answer)

    def _read_ack(self, ours: Commitment, answer: Record) -> Acknowledgement:
        """Their reply, as an acknowledgement of the digest we just sent.

        A reference opponent answers ``{"ok": true}`` with no digest. Rather
        than refuse to play against one, the digest we sent is used — we know
        what they received, because we sent it — and the step is recorded in
        :attr:`reference_acks` so the difference is visible instead of assumed.
        """
        acknowledges = answer.get("acknowledges")
        if not isinstance(acknowledges, str):
            self.reference_acks.append(ours.step)
            acknowledges = ours.commit
        return Acknowledgement(
            step=ours.step,
            sender=self.opponent,
            acknowledges=acknowledges,
            timestamp=self.now,
        )

    def await_commit(self, step: int) -> Commitment:
        turn = self._await_turn(step)
        return Commitment(
            step=turn.step,
            sender=turn.sender,
            commit=turn.commit,
            timestamp=turn.timestamp,
            game_uid=turn.game_uid,
            sub_game=turn.sub_game,
        )

    def send_ack(self, ack: Acknowledgement) -> None:
        """Nothing crosses the wire: our answer to *their* commit carried it."""

    def await_ack(self, step: int) -> Acknowledgement:
        ack = self.acks.get(step)
        if ack is None:
            raise PeerTimeout(
                f"no acknowledgement for step {step}; the {self.opponent} never answered "
                "our commitment, so nothing has locked and the reveal must not go out"
            )
        return ack

    def send_reveal(self, opened: Reveal) -> None:
        self._submit([opened.to_dict()], UNDECIDED)

    def await_reveal(self, step: int) -> Reveal:
        """The reveal for ``step``, which is bound to this sub-game by construction.

        The binding is enforced where a record that fails it can be *set aside*
        — :meth:`_hold_payload` — rather than here, where the only thing left to
        do with one is raise. Those are not the same outcome: a foreign record
        that ends the wait costs the sub-game just as surely as one that gets
        played, and it is the legitimate reveal queued behind it that pays.
        """
        return Reveal.from_dict(
            self._await_reveal_record(step),
            hint_max_words=self.hint_max_words,
        )

    def send_final(self, disclosed: FinalReveal) -> None:
        self._submit([disclosed.to_dict()], self.result_claim or UNDECIDED)

    def await_final(self) -> FinalReveal:
        return FinalReveal.from_dict(self._await_record(lambda r: "nonces" in r))

    def _submit(self, records: list[Record], result_claim: str) -> None:
        payload = AuditPayload(
            sender=self.role,
            records=records,
            result_claim=result_claim,
            game_uid=self.game_uid,
            sub_game=self.sub_game,
        )
        self.client.call("submit_audit", {"payload": payload.to_dict()})

    def _await_turn(self, step: int) -> TurnMessage:
        """The next commitment actually bound to the sub-game we are playing.

        Taking the head of the queue on trust is what let one packet that should
        never have been there cost the legitimate commitment behind it — the
        ceremony refuses the forgery, and nothing can put the real one back. A
        consumer that raised instead would lose the same sub-game by a longer
        route. So a foreign turn is set aside and the wait continues on the
        deadline it started with, which is what keeps skipping from becoming a
        second, unbudgeted wait.
        """
        deadline = time.monotonic() + self.timeout
        while True:
            turn: TurnMessage = self._drain(self.inboxes.turns, step, "commitment", deadline)
            if turn.game_uid == self.game_uid and turn.sub_game == self.sub_game:
                return turn
            self.quarantined.append(turn.to_dict())


def _install(namespace: dict[str, object]) -> None:
    globals().update(namespace)
