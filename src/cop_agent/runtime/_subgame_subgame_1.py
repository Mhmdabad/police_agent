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


class _SubGameMixin1:
    def __post_init__(self) -> None:
        self.ceremony = MatchCeremony(role=self.role)
        self.start = self.state
        self.belief = Belief.uniform(self.state)
        self.belief.exclude(position_of(self.state, self._agent(self.role)))

    @property
    def opponent(self) -> str:
        return OPPONENT_OF[self.role]

    def play(self) -> Played:
        """Run until capture or the step limit, then disclose every nonce.

        The loop stops the moment a capture is on the board rather than
        finishing the step count. A sub-game that continued past a capture
        would produce a log whose later steps describe a game that was already
        over, and two peers disagreeing about when it ended is a disagreement
        about the result.
        """
        if self._captured():
            self._disclose()
            return self._finished(0, captured=True, reason="capture")
        played = 0
        for step in range(1, self.max_steps + 1):
            played = step
            self._one_step(step)
            if self._captured():
                self._disclose()
                return self._finished(step, captured=True, reason="capture")
        self._disclose()
        return self._finished(played, captured=False, reason="step limit reached")

    def _finished(self, steps: int, *, captured: bool, reason: str) -> Played:
        self.play_result = Played(steps, self.state, captured, reason, self.audit())
        return self.play_result

    def _one_step(self, step: int) -> None:
        """Advance the board's own step counter *before* anything is sealed.

        ``step_record`` seals ``state.step``, and the Replay App checks that
        number against the slot the row was filed under — the anti-replay rule
        from #102. A loop that committed while the board still said ``step - 1``
        would produce a log in which every row seals the wrong number, and the
        stamp on every honest match this agent ever played would be
        ``TAMPERED``. It is the loop's job to keep the board and the ceremony
        counting the same thing.
        """
        self.state = advance_turn(self.state)
        self.sealed_states[step] = self.state
        record, action, opened = self._commit(step)
        self._acknowledge(step)
        self._reveal(step, record, opened)
        self._advance(action, self.peer_move(step))
        self._observe(step)
        self.scent.decay()


def _install(namespace: dict[str, object]) -> None:
    globals().update(namespace)
