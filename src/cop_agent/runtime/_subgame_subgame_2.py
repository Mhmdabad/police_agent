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


class _SubGameMixin2:
    def _commit(self, step: int) -> tuple[dict[str, object], Action, Reveal]:
        decision_state, context = self._strategy_input()
        try:
            signature(self.brain.decide).bind(decision_state, **context)
        except TypeError as exc:
            raise StrategyContextError(
                "configured brain decide() must accept **context containing "
                f"{next(iter(context))}, concentration, and uncertainty"
            ) from exc
        decision = self.brain.decide(decision_state, **context)
        if not decision.hint:
            decision = replace(decision, hint="I am watching the streets")
        try:
            require_hint({"hint": decision.hint}, max_words=self.hint_max_words)
        except InvalidPayloadError as exc:
            raise StrategyContextError(f"configured brain produced an invalid hint: {exc}") from exc
        action = decision.action
        self._our_actions[step] = action
        placed = action.at if isinstance(action, PlaceBarrier) else None
        move: Move | str = action.move if isinstance(action, MoveAction) else "barrier"
        laid = self._emit(action)
        record = step_record(
            self.state,
            self.role,
            move,
            decision.intent,
            decision.hint,
            placed,
            laid,
            game_uid=self.log.game_uid,
            sub_game=self.log.sub_game,
        )
        secret = nonce()
        commitment = Commitment(
            step=step,
            sender=self.role,
            commit=commit_of(record, secret),
            timestamp=self.now(),
            game_uid=self.log.game_uid,
            sub_game=self.log.sub_game,
        )
        self.ceremony.at(step).commit(commitment, secret)
        self.log.commit(step, commitment.commit)
        if decision.reasoning:
            self.log.discuss(step, {"intent": decision.intent, "reasoning": decision.reasoning})
        self.peer.send_commit(commitment)
        self.ceremony.at(step).receive(self.peer.await_commit(step))
        opened = Reveal(
            step=step,
            sender=self.role,
            move=move,
            intent=decision.intent,
            hint=decision.hint,
            timestamp=self.now(),
            game_uid=self.log.game_uid,
            sub_game=self.log.sub_game,
            barrier_placed=list(placed) if placed else None,
            scent=laid,
        )
        return record, action, opened

    def _strategy_input(self) -> tuple[BoardState, dict[str, object]]:
        self.belief.apply_barriers(self.state)
        self.belief.exclude(position_of(self.state, self._agent(self.role)))
        peak = self.belief.most_likely()
        if peak is None:
            raise StrategyContextError("opponent belief has no possible cell")
        concentration = self.belief.concentration()
        state = (
            replace(self.state, thief=peak)
            if self.role == "police"
            else replace(self.state, cop=peak)
        )
        focus = "target" if self.role == "police" else "threat"
        return state, {
            focus: peak,
            "concentration": concentration,
            "uncertainty": 1.0 - concentration,
        }


def _install(namespace: dict[str, object]) -> None:
    globals().update(namespace)
