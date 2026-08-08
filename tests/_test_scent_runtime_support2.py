from __future__ import annotations
import json
from dataclasses import replace
from typing import Any, Protocol
import pytest
from cop_agent.domain.actions import MoveAction
from cop_agent.domain.axes import AxisConvention
from cop_agent.domain.board import BoardState
from cop_agent.domain.crypto import commit_of, nonce, step_record
from cop_agent.domain.memory import ScentMemory
from cop_agent.domain.scent import CENTRE_INTENSITY
from cop_agent.domain.trail import RETENTION
from cop_agent.infra.ceremony import (
    Acknowledgement,
    Commitment,
    FinalReveal,
    MatchCeremony,
    Reveal,
)
from cop_agent.infra.match_log import MatchLog
from cop_agent.runtime.subgame import SubGame
from cop_agent.strategy.base import Decision, StrategyContextError
from cop_agent.strategy.police_brain import PoliceBrain
WHEN = "2026-08-05T10:00:00+00:00"
AXES = AxisConvention()
GRID = 8
OUR_ROLE = "police"
THEIR_ROLE = "thief"
OUR_START = (0, 0)
THEIR_START = (6, 5)
AWAY = "S"
TWO_AWAY = (2, 0)
FORGED_FIELD = {"0,1": 0.9, "0,0": 0.62}
class ScentedOpponent:
    def __init__(self, forge_at: int | None = None, omit: bool = False, junk: bool = False) -> None:
        self.role = THEIR_ROLE
        self.forge_at = forge_at
        self.omit = omit
        self.junk = junk
        self.ceremony = MatchCeremony(role=self.role)
        self.scent = ScentMemory()
        self.fields: dict[int, dict[str, float]] = {}
        self.nonces: dict[int, str] = {}
        self.state = board()
        self.commits: list[Commitment] = []
    @property
    def cell(self) -> tuple[int, int]:
        return THEIR_START
    def send_commit(self, commitment: Commitment) -> None:
        self.game_uid, self.sub_game = commitment.game_uid, commitment.sub_game
        self.commits.append(Commitment.from_dict(self._wire(commitment)))
        self.ceremony.at(commitment.step).receive(self.commits[-1])
    def await_commit(self, step: int) -> Commitment:
        if step > 1:
            self.scent.decay()  # once per full turn, at the boundary we just crossed
        self.scent.emit(self.cell, GRID)
        self.fields[step] = self.scent.outgoing()
        self.state = replace(self.state, step=step)
        record = step_record(
            self.state,
            self.role,
            "STAY",
            "truth",
            f"t{step}",
            scent=self.sealed(step),
            game_uid=self.game_uid,
            sub_game=self.sub_game,
        )
        secret = nonce()
        self.nonces[step] = secret
        mine = Commitment(
            step=step,
            sender=self.role,
            commit=commit_of(record, secret),
            timestamp=WHEN,
            game_uid=self.game_uid,
            sub_game=self.sub_game,
        )
        self.ceremony.at(step).commit(mine, secret)
        return Commitment.from_dict(self._wire(mine))
    def sealed(self, step: int) -> dict[str, float] | None:
        return None if self.omit else self.fields[step]
    def spoken(self, step: int) -> dict[str, float] | None:
        if self.omit:
            return None
        if self.junk:
            return {"99,99": 4.2}
        if step == self.forge_at:
            return FORGED_FIELD
        return self.fields[step]
    def send_ack(self, ack: Acknowledgement) -> None:
        self.ceremony.at(ack.step).receive_ack(Acknowledgement.from_dict(self._wire(ack)))
    def await_ack(self, step: int) -> Acknowledgement:
        return Acknowledgement.from_dict(self._wire(self.ceremony.at(step).acknowledge(WHEN)))
    def send_reveal(self, opened: Reveal) -> None:
        self.ceremony.at(opened.step).receive_reveal(Reveal.from_dict(self._wire(opened)))
    def await_reveal(self, step: int) -> Reveal:
        mine = Reveal(
            step=step,
            sender=self.role,
            move="STAY",
            intent="truth",
            hint=f"t{step}",
            timestamp=WHEN,
            scent=self.spoken(step),
            game_uid=self.game_uid,
            sub_game=self.sub_game,
        )
        self.ceremony.at(step).reveal(mine)
        return Reveal.from_dict(self._wire(mine))
    def send_final(self, disclosed: FinalReveal) -> None:
        self.ceremony.receive_final_reveal(FinalReveal.from_dict(self._wire(disclosed)))
    def await_final(self) -> FinalReveal:
        self.ceremony.finish()
        return FinalReveal.from_dict(self._wire(self.ceremony.final_reveal(WHEN)))
    @staticmethod
    def _wire(message: Wireable) -> dict[str, Any]:
        body: dict[str, Any] = json.loads(json.dumps(message.to_dict()))
        return body

def _install(namespace: dict[str, object]) -> None:
    globals().update(namespace)
