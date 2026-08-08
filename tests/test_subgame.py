import json
from dataclasses import replace
from pathlib import Path
from typing import Any, Protocol
import pytest
from cop_agent.domain.actions import MoveAction, PlaceBarrier, apply_action
from cop_agent.domain.axes import AxisConvention
from cop_agent.domain.board import BoardState
from cop_agent.domain.crypto import commit_of, nonce, step_record
from cop_agent.domain.memory import ScentMemory
from cop_agent.infra.ceremony import (
    Acknowledgement,
    Commitment,
    FinalReveal,
    MatchCeremony,
    Reveal,
    Verdict,
)
from cop_agent.infra.match_log import MatchLog
from cop_agent.runtime.subgame import SubGame, UnplayableReveal
from cop_agent.strategy.base import Decision
from cop_agent.strategy.police_brain import PoliceBrain
from cop_agent.ui.replay import load
from cop_agent.ui.verdict import Stamp, walk
class Wireable(Protocol):
    def to_dict(self) -> dict[str, Any]: ...
WHEN = "2026-08-05T10:00:00+00:00"
AXES = AxisConvention()
def board(
    grid: int = 8, cop: tuple[int, int] = (0, 0), thief: tuple[int, int] = (6, 5)
) -> BoardState:
    return BoardState(grid_size=grid, cop=cop, thief=thief, barriers=frozenset(), step=0)
class StandInOpponent:
    def __init__(self, move: str = "STAY", corrupt_at: int | None = None) -> None:
        self.role = "thief"
        self.move = move
        self.corrupt_at = corrupt_at
        self.ceremony = MatchCeremony(role=self.role)
        self.records: dict[int, dict[str, object]] = {}
        self.nonces: dict[int, str] = {}
        self.fields: dict[int, dict[str, float]] = {}
        self.scent = ScentMemory()
        self.seen: list[str] = []
        self.state = board()
    def send_commit(self, commitment: Commitment) -> None:
        self.seen.append("commit")
        self.game_uid, self.sub_game = commitment.game_uid, commitment.sub_game
        self.ceremony.at(commitment.step).receive(Commitment.from_dict(self._wire(commitment)))
    def await_commit(self, step: int) -> Commitment:
        self.state = replace(self.state, step=step)
        if step > 1:
            self.scent.decay()
        self.scent.emit(self.state.thief, self.state.grid_size)
        self.fields[step] = self.scent.outgoing()
        record = step_record(
            self.state,
            self.role,
            self.move,
            "truth",
            f"t{step}",
            scent=self.fields[step],
            game_uid=self.game_uid,
            sub_game=self.sub_game,
        )
        secret = nonce()
        self.records[step], self.nonces[step] = record, secret
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
    def send_ack(self, ack: Acknowledgement) -> None:
        self.seen.append("ack")
        self.ceremony.at(ack.step).receive_ack(Acknowledgement.from_dict(self._wire(ack)))
    def await_ack(self, step: int) -> Acknowledgement:
        return Acknowledgement.from_dict(self._wire(self.ceremony.at(step).acknowledge(WHEN)))
    def send_reveal(self, opened: Reveal) -> None:
        self.seen.append("reveal")
        self.ceremony.at(opened.step).receive_reveal(Reveal.from_dict(self._wire(opened)))
        action = (
            PlaceBarrier(at=(opened.barrier_placed[0], opened.barrier_placed[1]))
            if opened.barrier_placed
            else MoveAction(move=opened.move)  # type: ignore[arg-type]
        )
        self.state = apply_action(self.state, "cop", action, AXES)
    def await_reveal(self, step: int) -> Reveal:
        spoken = "N" if step == self.corrupt_at else self.move
        mine = Reveal(
            step=step,
            sender=self.role,
            move=spoken,
            intent="truth",
            hint=f"t{step}",
            timestamp=WHEN,
            scent=self.fields[step],
            game_uid=self.game_uid,
            sub_game=self.sub_game,
        )
        self.ceremony.at(step).reveal(mine)
        return Reveal.from_dict(self._wire(mine))
    def send_final(self, disclosed: FinalReveal) -> None:
        self.seen.append("final")
        self.ceremony.receive_final_reveal(FinalReveal.from_dict(self._wire(disclosed)))
    def await_final(self) -> FinalReveal:
        self.ceremony.finish()
        return FinalReveal.from_dict(self._wire(self.ceremony.final_reveal(WHEN)))
    @staticmethod
    def _wire(message: Wireable) -> dict[str, Any]:
        body: dict[str, Any] = json.loads(json.dumps(message.to_dict()))
        return body
def a_subgame(
    tmp_path: Path,
    opponent: StandInOpponent | None = None,
    max_steps: int = 4,
    state: BoardState | None = None,
) -> tuple[SubGame, StandInOpponent, MatchLog]:
    peer = opponent or StandInOpponent()
    log = MatchLog(
        game_id="uoh26-s82kma9e",
        sub_game=1,
        role="police",
        game_uid="u-0001",
        config_sha256="c" * 64,
    )
    game = SubGame(
        role="police",
        brain=PoliceBrain(),
        peer=peer,
        log=log,
        state=state or board(),
        axes=AXES,
        max_steps=max_steps,
        now=lambda: WHEN,
    )
    return game, peer, log
