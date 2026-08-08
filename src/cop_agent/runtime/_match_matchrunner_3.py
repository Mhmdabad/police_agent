# mypy: ignore-errors
# ruff: noqa
from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from ..domain.axes import AxisConvention
from ..domain.board import BoardState
from ..domain.lock import ScentAgreement
from ..domain.outcome import TechnicalLoss
from ..domain.scoring import Outcome, scores_for
from ..infra.artefacts import ArtefactSet
from ..infra.ceremony import AuditResult
from ..infra.config_file import LockedConfig, lock
from ..infra.declaration import MatchDeclaration
from ..infra.handshake import Peering
from ..infra.match_log import MatchLog
from ..infra.report import Report, Repositories, SubGameResult
from ..shared.config import config_sha256, series_length
from ..strategy.base import BrainBase
from .orchestrator import (
    CONFIG_TIMEOUT_SEC,
    GREETING_TIMEOUT_SEC,
    MatchAborted,
    Orchestrator,
)
from .peer import McpPeer
from .subgame import Played, SubGame


class _MatchRunnerMixin3:
    def play_sub_game(self, number: int, timeout: float = 30.0) -> SubGameOutcome:
        locked = self.locked_scent()
        self.orchestrator.inboxes.bind(self.declaration.game_uid, number)
        hint_max_words = int(self.parameters.get("hint_max_words", 15))
        self.orchestrator.inboxes.hint_max_words = hint_max_words
        log = MatchLog(
            game_id=self.game_id,
            sub_game=number,
            role=self.role,
            game_uid=self.declaration.game_uid,
            config_sha256=config_sha256(self.parameters),
        )
        game = SubGame(
            role=self.role,
            brain=self.brain,
            peer=McpPeer(
                role=self.role,
                client=self.orchestrator.client,
                inboxes=self.orchestrator.inboxes,
                now=self.now(),
                timeout=timeout,
                hint_max_words=hint_max_words,
                game_uid=self.declaration.game_uid,
                sub_game=number,
            ),
            log=log,
            state=self.start,
            axes=self.axes,
            max_steps=self.max_steps,
            hint_max_words=hint_max_words,
            now=self.now,
            require_bound_scent=locked.require_bound_scent,
        )
        played = game.play()
        outcome = SubGameOutcome(
            number=number, played=played, audit=game.audit(), log=log, game=game
        )
        self.outcomes.append(outcome)
        return outcome

    def result(
        self, commit_hash: str, total_tokens: int, agreed: bool, repositories: Repositories
    ) -> Report:
        return Report(
            game_id=self.game_id,
            game_uid=self.declaration.game_uid,
            role=self.role,
            team=self.declaration.us.name,
            opponent_team=self.declaration.them.name,
            repositories=repositories,
            sub_games=tuple(
                SubGameResult(
                    sub_game=outcome.number,
                    cop_score=outcome.scores()[0],
                    thief_score=outcome.scores()[1],
                    commit_hash=commit_hash,
                    steps=outcome.played.steps,
                )
                for outcome in self.outcomes
            ),
            total_tokens=total_tokens,
            agreed=agreed,
            started_at=self.declaration.started_at,
            ended_at=self.now(),
        )

    def artefacts(self, result: Report) -> ArtefactSet:
        return ArtefactSet(
            declaration=self.declaration,
            configs=tuple(self.config_for(o.number) for o in self.outcomes),
            logs=tuple(o.log for o in self.outcomes),
            result=result,
        )

    def write(self, result: Report) -> tuple[Path, ...]:
        return self.artefacts(result).write(self.directory)


def _install(namespace: dict[str, object]) -> None:
    globals().update(namespace)
