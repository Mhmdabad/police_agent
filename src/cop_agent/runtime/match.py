# mypy: ignore-errors
# ruff: noqa
from ._match_matchrunner_1 import _MatchRunnerMixin1, _install as _install_match_matchrunner_1
from ._match_matchrunner_2 import _MatchRunnerMixin2, _install as _install_match_matchrunner_2
from ._match_matchrunner_3 import _MatchRunnerMixin3, _install as _install_match_matchrunner_3
from ._match_matchrunner_4 import _MatchRunnerMixin4, _install as _install_match_matchrunner_4
from ._match_subgameoutcome_1 import _SubGameOutcomeMixin1, _install as _install_match_subgameoutcome_1
"""A whole match against a live opponent: handshake, agree, play, audit, record.

The last thing between a pile of working components and a game against another
team. Everything below existed and had no caller — ``open_series`` traded
addresses, ``agree_config`` compared digests, ``SubGame`` played, ``ArtefactSet``
wrote the evidence — and nothing ran them in order.

The order is not negotiable and each step exists because skipping it costs a
match:

1. **Handshake** — trade public addresses and write both into the declaration.
   The address in the private config is only a bootstrap; what the opponent
   *announces* is where they are.
2. **Agree the config** — exchange ``config_sha256`` and refuse to play on any
   mismatch. Two peers with different parameters are playing different games
   and will report incompatible results, which scores zero for both.
3. **Play** — each sub-game through the four ceremony phases.
4. **Audit** — re-derive every step the opponent committed to, once their
   nonces arrive. This is the only moment the question is answerable.
5. **Score** — classify the final board through :mod:`..domain.scoring`, whose
   table comes from Appendix F. The scores are *fixed* parameters: inventing
   them here, or carrying a placeholder into a result file, is a deviation an
   audit finds.
6. **Record** — the four artefacts, checked for coherence before anything is
   written.

**Nothing here mails anybody.** The report is built and written to disk; sending
it is a separate, deliberate act by a person who has agreed the result with the
opponent first (FR-7.16). A match runner that mailed on completion would send a
report for a result the other side had not yet accepted.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..domain.axes import AxisConvention
from ..domain.board import BoardState
from ..domain.lock import ScentAgreement
from ..infra.ceremony import AuditResult
from ..infra.declaration import MatchDeclaration
from ..infra.handshake import Peering
from ..infra.match_log import MatchLog
from ..strategy.base import BrainBase
from .orchestrator import (
    Orchestrator,
)
from .subgame import Played, SubGame


@dataclass(frozen=True, slots=True)
class SubGameOutcome(_SubGameOutcomeMixin1):
    """One sub-game, and what we concluded about the other side's play."""

    number: int
    played: Played
    audit: AuditResult
    log: MatchLog
    game: "SubGame | None" = None
    """The sub-game that produced this, for anything wanting its ceremony.

    Optional because an outcome can be reconstructed from files without one.
    """




@dataclass
class MatchRunner(_MatchRunnerMixin1, _MatchRunnerMixin2, _MatchRunnerMixin3, _MatchRunnerMixin4):
    """Plays a whole match against one opponent."""

    orchestrator: Orchestrator
    declaration: MatchDeclaration
    parameters: dict[str, Any]
    brain: BrainBase
    axes: AxisConvention
    start: BoardState
    max_steps: int
    directory: Path
    now: Callable[[], str] = field(default=lambda: "")
    peering: Peering | None = None
    """The addresses in force, from the opening handshake and re-agreed at each boundary.

    Supplied by the driver rather than negotiated here: trading addresses is
    :meth:`Orchestrator.open_series`, and a runner that opened its own series
    would be a second place the declaration gets written. What the runner owns
    is the *series*, which is why the boundaries between its sub-games are its
    responsibility and this field advances across them.

    ``None`` means no addresses were ever agreed, and :meth:`play_series`
    refuses on it rather than skipping the boundary. Skipping it silently is
    exactly the defect this field exists to close.
    """

    outcomes: list[SubGameOutcome] = field(default_factory=list, init=False)

    scent_lock: ScentAgreement | None = field(default=None, init=False)
    """The pre-series scent model both sides hashed, once :meth:`agree` has run.

    ``None`` until a peer has matched our lock exactly, and not settable from
    outside the runner's construction: a series that never negotiated one has
    nothing to derive its scent rules from, and :meth:`play_sub_game` refuses to
    open on that rather than picking a default. The default is what P1-15 was.
    """


_install_match_matchrunner_1(globals())
_install_match_matchrunner_2(globals())
_install_match_matchrunner_3(globals())
_install_match_matchrunner_4(globals())
_install_match_subgameoutcome_1(globals())
