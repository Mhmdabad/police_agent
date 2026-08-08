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


class _SubGameMixin4:
    def _advance(self, ours: Action, theirs: Action | None) -> None:
        self.state = apply_action(self.state, self._agent(self.role), ours, self.axes)
        if theirs is not None:
            self.state = apply_action(self.state, self._agent(self.opponent), theirs, self.axes)

    @staticmethod
    def _agent(role: str) -> Agent:
        return "cop" if role == "police" else "thief"

    def _captured(self) -> bool:
        return (
            is_capture_by_overlap(self.state)
            or is_trapping_capture(self.state)
            or is_enclosure_capture(self.state, self.axes)
        )

    def _disclose(self) -> None:
        self.ceremony.finish()
        disclosed = self.ceremony.final_reveal(self.now())
        for step, secret in disclosed.nonces.items():
            self.log.disclose(step, secret)
        self.peer.send_final(disclosed)
        self.their_final = self.ceremony.receive_final_reveal(self.peer.await_final())

    def audit(self) -> AuditResult:
        if self.their_final is None:
            return AuditResult(
                verdict=Verdict.FORGED,
                checked=0,
                failures=(
                    f"the {self.opponent} disclosed no nonces, so nothing they committed "
                    "to can be opened; their play is unverifiable rather than proven",
                ),
            )
        sealed = audit_opponent(self.ceremony, self.their_final, self.sealed_states)
        impossible = self._audit_scent()
        if not impossible:
            return sealed
        return AuditResult(
            verdict=Verdict.FORGED,
            checked=sealed.checked,
            failures=sealed.failures + impossible,
        )

    def _audit_scent(self) -> tuple[str, ...]:
        plays = [
            StepPlay(
                step=step,
                ours=action,
                theirs=self.peer_move(step),
                disclosed=opened.scent if (opened := self._peer_reveals.get(step)) else None,
            )
            for step, action in sorted(self._our_actions.items())
        ]
        return audit_scent(
            self.start,
            self.axes,
            self.role,
            plays,
            require_bound=self.require_bound_scent,
        )


def _install(namespace: dict[str, object]) -> None:
    globals().update(namespace)
