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


class _PeerMixin1:
    def send_commit(self, commitment: Commitment) -> None: ...
    def await_commit(self, step: int) -> Commitment: ...
    def send_ack(self, ack: Acknowledgement) -> None: ...
    def await_ack(self, step: int) -> Acknowledgement: ...
    def send_reveal(self, opened: Reveal) -> None: ...
    def await_reveal(self, step: int) -> Reveal: ...
    def send_final(self, disclosed: FinalReveal) -> None: ...
    def await_final(self) -> FinalReveal: ...


def _install(namespace: dict[str, object]) -> None:
    globals().update(namespace)
