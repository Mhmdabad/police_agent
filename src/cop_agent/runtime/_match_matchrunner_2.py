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


class _MatchRunnerMixin2:
    def rehandshake(self, number: int, timeout: float = GREETING_TIMEOUT_SEC) -> Peering:
        """Re-agree the addresses at the boundary before sub-game ``number``.

        The addresses we announce are the ones already agreed: our own tunnel
        rotating is a discovery the driver makes, not something a series loop
        can invent. What this recovers from is *their* tunnel rotating, which is
        the case the loop can neither predict nor be told about — and it is the
        common one, because a free-tier tunnel issues a new URL on every restart.

        The result replaces :attr:`peering` only once it is agreed, so a refused
        boundary leaves the series pointing where it was rather than half-moved.

        **The mailboxes cross the boundary before the announcement does.** The
        announcement is what tells the opponent we have reached ``number``, and
        they open the sub-game by sending into our door, so a door bound after
        the announcement is one we have invited a message through before opening
        it. That is the same window that let a packet in before any binding
        existed, one boundary further along, and it is closed the same way:
        by saying where we are only once we can act on the answer.
        """
        self.orchestrator.inboxes.bind(self.declaration.game_uid, number)
        current = self.peered()
        self.peering = self.orchestrator.rehandshake(
            current, current.ours, number, self.directory, self.game_id, timeout
        )
        return self.peering

    def play_series(self, timeout: float = 30.0) -> list[SubGameOutcome]:
        """Step 3 for the whole series: every numbered sub-game, in order.

        The length is resolved *before* the first sub-game, so a configuration
        that deviates costs nothing — no board is played under it, and the
        opponent never sees a series that stops short of the book.

        **Every pair of sub-games is separated by a re-handshake**, which is the
        thing this loop had none of. ``rehandshake`` was written, documented and
        never called: six sub-games ran back to back, so a tunnel that rotated
        partway through killed the series — and a technical loss scores zero for
        *both* sides, so it destroyed the sub-games already won on the board too.

        Five boundaries, at 1→2 through 5→6. Not before the first, which the
        opening handshake already covered, and not after the last, where an
        announcement is a message nobody is waiting for.

        The peering is resolved alongside the length and for the same reason: a
        series that cannot re-handshake is one that will lose a board it has
        already won, and the cheapest moment to say so is before there is a
        board to lose. The length goes first of the two because a deviating
        configuration is a fault of our own that needs no opponent to diagnose.
        """
        length = self.sub_games
        self.peered()
        played: list[SubGameOutcome] = []
        for number in range(1, length + 1):
            if number > 1:
                self.rehandshake(number, timeout)
            played.append(self.play_sub_game(number, timeout))
        return played


def _install(namespace: dict[str, object]) -> None:
    globals().update(namespace)
