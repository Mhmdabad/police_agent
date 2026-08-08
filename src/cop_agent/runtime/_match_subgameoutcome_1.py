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


class _SubGameOutcomeMixin1:
    @property
    def clean(self) -> bool:
        return self.audit.clean

    @property
    def outcome(self) -> Outcome:
        """How this sub-game finished, in the rulebook's vocabulary."""
        return Outcome.CAPTURE if self.played.captured else Outcome.SURVIVAL

    def scores(self) -> tuple[int, int]:
        """``(cop, thief)`` for this sub-game, from the Appendix F table."""
        return scores_for(self.outcome)


def _install(namespace: dict[str, object]) -> None:
    globals().update(namespace)
