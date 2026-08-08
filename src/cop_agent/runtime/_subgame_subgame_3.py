# mypy: ignore-errors
# ruff: noqa
from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from inspect import signature
from typing import Protocol, cast
from ..domain.actions import Action, MoveAction, PlaceBarrier, apply_action
from ..domain.axes import AxisConvention
from ..domain.belief import Belief
from ..domain.board import Agent, BoardState, Move
from ..domain.crypto import commit_of, nonce, step_record
from ..domain.inference import update as absorb_evidence
from ..domain.memory import ScentMemory
from ..domain.outcome import is_capture_by_overlap, is_enclosure_capture, is_trapping_capture
from ..domain.rules import advance_turn, position_of
from ..domain.scent_audit import ScentFieldError, StepPlay, audit_scent, check_field
from ..infra.ceremony import (
    Acknowledgement,
    AuditResult,
    Commitment,
    FinalReveal,
    MatchCeremony,
    Reveal,
    Verdict,
    audit_opponent,
)
from ..infra.match_log import MatchLog
from ..infra.validation import InvalidPayloadError, require_hint
from ..strategy.base import BrainBase, StrategyContextError

OPPONENT_OF = {"police": "thief", "thief": "police"}
MOVES: frozenset[str] = frozenset({"N", "S", "E", "W", "STAY"})


class _SubGameMixin3:
    def _emit(self, action: Action) -> dict[str, float]:
        agent = self._agent(self.role)
        after = apply_action(self.state, agent, action, self.axes)
        self.scent.emit(position_of(after, agent), self.state.grid_size)
        return self.scent.outgoing()

    def _observe(self, step: int) -> None:
        self.belief.apply_barriers(self.state)
        opened = self._peer_reveals.get(step)
        if opened is None or opened.scent is None:
            return
        try:
            check_field(opened.scent, self.state.grid_size)
        except ScentFieldError:
            return
        plays = [
            StepPlay(
                step=played_step,
                ours=action,
                theirs=self.peer_move(played_step),
                disclosed=reveal.scent if (reveal := self._peer_reveals.get(played_step)) else None,
            )
            for played_step, action in sorted(self._our_actions.items())
            if played_step <= step
        ]
        failures = audit_scent(
            self.start,
            self.axes,
            self.role,
            plays,
            require_bound=self.require_bound_scent,
        )
        if any(
            failure.startswith(f"step {step}:") or "revealed move cannot be replayed" in failure
            for failure in failures
        ):
            return
        self.scent.absorb(opened.scent, self.state.grid_size)
        absorb_evidence(self.belief, self.scent.opponent.values)

    def _acknowledge(self, step: int) -> None:
        self.peer.send_ack(self.ceremony.at(step).acknowledge(self.now()))
        self.ceremony.at(step).receive_ack(self.peer.await_ack(step))

    def _reveal(self, step: int, record: dict[str, object], opened: Reveal) -> None:
        self.ceremony.at(step).reveal(opened)
        self.log.reveal(step, record)
        self.peer.send_reveal(opened)
        self._peer_reveals[step] = self.ceremony.at(step).receive_reveal(
            self.peer.await_reveal(step)
        )
        self.received_hints[step] = self._peer_reveals[step].hint

    def peer_move(self, step: int) -> Action | None:
        opened = self._peer_reveals.get(step)
        if opened is None:
            return None
        if opened.barrier_placed:
            if self.opponent != "police":
                raise UnplayableReveal(
                    f"the thief revealed a barrier at step {step}; only the cop may place "
                    "one, and a board advanced by an illegal action is a board the two "
                    "peers no longer share"
                )
            return PlaceBarrier(at=(opened.barrier_placed[0], opened.barrier_placed[1]))
        if opened.move not in MOVES:
            raise UnplayableReveal(
                f"the {self.opponent} revealed move {opened.move!r} at step {step}, which is "
                "not a move; the board cannot be advanced from a statement it cannot read"
            )
        return MoveAction(move=cast("Move", opened.move))


def _install(namespace: dict[str, object]) -> None:
    globals().update(namespace)
