from dataclasses import dataclass
from typing import Any
import pytest
from cop_agent.domain.actions import MoveAction
from cop_agent.domain.board import Agent, BoardState, Move
from cop_agent.infra.ceremony import CeremonyError, Reveal
from cop_agent.infra.inboxes import RETRY_KEY, PeerInboxes
from cop_agent.infra.mcp_client import (
    ClientSettings,
    OpponentClient,
    OpponentUnreachableError,
    PeerNotReadyError,
)
from cop_agent.strategy.base import BrainBase, Decision
@dataclass
class StayingBrain(BrainBase):
    @property
    def role(self) -> Agent:
        return "cop"
    def _pick_move(self, state: BoardState, **context: object) -> Move:
        return "STAY"
def reveal(**changes: object) -> dict[str, object]:
    body: dict[str, object] = {
        "step": 1,
        "sender": "thief",
        "move": "STAY",
        "intent": "lie",
        "hint": "I slipped south past the bridge",
        "barrier_placed": None,
        "scent": {},
        "timestamp": "2026-08-07T00:00:00Z",
        "game_uid": "series-123",
        "sub_game": 2,
    }
    body.update(changes)
    return body
OPPONENT = str(reveal()["sender"])
"""Whoever the other side is here. Taken from the fixture so both repos read alike."""
def turn(**changes: object) -> dict[str, object]:
    body: dict[str, object] = {
        "step": 1,
        "sender": OPPONENT,
        "hint": "",
        "smell_grid": {},
        "commit": "a" * 64,
        "timestamp": "now",
        "game_uid": "series-123",
        "sub_game": 2,
    }
    body.update(changes)
    return body
def audit(records: list[dict[str, object]], **changes: object) -> dict[str, object]:
    body: dict[str, object] = {
        "sender": OPPONENT,
        "records": records,
        "result_claim": "in_progress",
        "game_uid": "series-123",
        "sub_game": 2,
    }
    body.update(changes)
    return body
@dataclass
class Door:
    inboxes: PeerInboxes
    def call(self, url: str, tool: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
        return self.inboxes.receive_turn(payload["message"])
DEFERRED = {"ok": False, RETRY_KEY: True}
"""What a door that is not open *yet* answers, minus the human-readable detail."""
def deferred(answer: dict[str, object]) -> bool:
    return {key: answer[key] for key in DEFERRED} == DEFERRED
