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


class _MatchRunnerMixin4:
    @property
    def opponent_played_fairly(self) -> bool:
        """Whether every sub-game audited clean.

        A match with one forged sub-game is not a match with a bad sub-game.
        FR-7.16 requires both sides to agree the result before either reports,
        and there is nothing to agree about a series where one side's
        commitments do not open.
        """
        return all(outcome.clean for outcome in self.outcomes)

    def failures(self) -> list[str]:
        """Every audit finding across the match, for the conversation that follows."""
        return [
            f"sub-game {outcome.number}: {failure}"
            for outcome in self.outcomes
            for failure in outcome.audit.failures
        ]


def _install(namespace: dict[str, object]) -> None:
    globals().update(namespace)
