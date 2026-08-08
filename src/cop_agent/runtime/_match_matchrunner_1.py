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


class _MatchRunnerMixin1:
    @property
    def game_id(self) -> str:
        return self.declaration.game_id

    @property
    def sub_games(self) -> int:
        return series_length(self.parameters)

    @property
    def role(self) -> str:
        return self.orchestrator.role

    def agree(self, timeout: float = CONFIG_TIMEOUT_SEC) -> str:
        self.orchestrator.inboxes.bind(self.declaration.game_uid, 1)
        digest = self.orchestrator.agree_config(
            self.parameters, game_uid=self.declaration.game_uid, timeout=timeout
        )
        self.scent_lock = self.orchestrator.agree_scent_model(
            game_uid=self.declaration.game_uid, timeout=timeout
        )
        return digest

    def locked_scent(self) -> ScentAgreement:
        if self.scent_lock is None:
            raise MatchAborted(
                TechnicalLoss.ILLEGAL_ACTION,
                "no scent-emission model was locked with the opponent; Appendix E "
                "rule 23 fixes it cryptographically before the game starts, and a "
                "sub-game opened without one is played on a field neither side can "
                "check — call agree() before playing",
            )
        return self.scent_lock

    def config_for(self, number: int) -> LockedConfig:
        return lock(
            game_id=self.game_id,
            game_uid=self.declaration.game_uid,
            sub_game=number,
            parameters=self.parameters,
            agreed_between=(self.declaration.us.name, self.declaration.them.name),
        )

    def peered(self) -> Peering:
        if self.peering is None:
            raise MatchAborted(
                TechnicalLoss.ILLEGAL_ACTION,
                "no addresses were agreed with the opponent; a series opens by "
                "trading greetings through open_series, and one that skipped it "
                "has nothing to re-handshake against between its sub-games",
            )
        return self.peering


def _install(namespace: dict[str, object]) -> None:
    globals().update(namespace)
