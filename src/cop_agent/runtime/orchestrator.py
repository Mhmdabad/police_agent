# mypy: ignore-errors
# ruff: noqa
from ._orchestrator_orchestrator_1 import _OrchestratorMixin1, _install as _install_orchestrator_orchestrator_1
from ._orchestrator_orchestrator_2 import _OrchestratorMixin2, _install as _install_orchestrator_orchestrator_2
from ._orchestrator_orchestrator_3 import _OrchestratorMixin3, _install as _install_orchestrator_orchestrator_3
from ._orchestrator_orchestrator_4 import _OrchestratorMixin4, _install as _install_orchestrator_orchestrator_4
from ._orchestrator_orchestrator_5 import _OrchestratorMixin5, _install as _install_orchestrator_orchestrator_5
from ._orchestrator_orchestrator_6 import _OrchestratorMixin6, _install as _install_orchestrator_orchestrator_6
"""The single gateway to every subsystem.

Appendix E rule 3: the orchestrator is the **only** entry point to the
subsystems, and peripheral modules never reference one another. That is not
architectural taste — a decision module that reaches directly into the MCP
connector cannot be replaced without touching both, and the rulebook grades
the ability to swap one component in isolation.

It **coordinates and does not decide**. No game rule lives here; move choice
belongs to the strategy module, legality to the domain layer, transport to the
connector. What lives here is the wiring between them and the conversion of a
subsystem failure into a recorded outcome.

Inbound traffic goes to :class:`~..infra.inboxes.PeerInboxes`, which is the
surface an opponent actually calls. The orchestrator routes into those
mailboxes; it does not re-validate, because two validators that disagree are
worse than one.
"""

from collections.abc import Callable
from dataclasses import dataclass, field

from ..domain.outcome import TechnicalLoss
from ..infra.inboxes import PeerInboxes
from ..infra.mcp_client import OpponentClient

PROTOCOL_VERSION = "1.0"
"""Bumped when the wire contract changes. Exchanged during negotiation."""

GREETING_TIMEOUT_SEC = 30.0
"""How long to wait for the opponent's address before declaring a timeout.

The Appendix F response timeout. A handshake with no deadline is the one place
a deadlock costs nothing to reach and everything to diagnose: neither peer has
moved, so there is no board state to explain what happened."""

CONFIG_TIMEOUT_SEC = 30.0
"""How long to wait for the opponent's config digest.

The same Appendix F response timeout, for the same reason: nobody has moved
yet, so an unbounded wait here produces a hang with no board to explain it. An
opponent who never answers has not agreed to our parameters, and the only safe
reading of silence at this gate is refusal."""

SCENT_TIMEOUT_SEC = 30.0
"""How long to wait for the opponent's scent-model offer.

The Appendix F response timeout again, and the same reading of silence. A peer
that will not lock the emission model has not agreed to one, and Appendix E rule
23 voids a match played on a model the two sides never fixed — so waiting longer
only delays a series that cannot legitimately open."""


@dataclass
class MatchAborted(Exception):
    """A subsystem failure ended the sub-game.

    Carries the cause rather than only the fact. Both teams must **agree** a
    result before either may report it, and "technical loss" with no cause is
    far harder to agree on than "timeout at step 12" — so the cause is recorded
    at the point it is known, not reconstructed afterwards.

    **Neither frozen nor slotted, and both for the same reason.** Python sets
    ``__traceback__`` on an exception as it propagates. ``slots=True`` leaves
    nowhere to put it; ``frozen=True`` generates a ``__setattr__`` that refuses
    it. Either way the interpreter discards the exception mid-flight and raises
    something else in its place — a ``TypeError`` about class identity, or a
    ``FrozenInstanceError`` — so the named cause this class exists to carry is
    precisely what gets destroyed.

    Worse, it only happens when a ``@contextlib.contextmanager`` is somewhere
    in the call path, which is why it survived until an acceptance test used a
    fixture. Immutability here was decorative: ``cause`` and ``detail`` are
    written once at the raise site and read at the catch site. An exception
    that cannot be raised is not a trade worth making.
    """

    cause: TechnicalLoss
    detail: str = ""




@dataclass
class Orchestrator(
    _OrchestratorMixin1,
    _OrchestratorMixin2,
    _OrchestratorMixin3,
    _OrchestratorMixin4,
    _OrchestratorMixin5,
    _OrchestratorMixin6,
):
    """Coordinates the subsystems behind one entry point."""

    inboxes: PeerInboxes
    client: OpponentClient
    role: str = "police"
    on_event: Callable[[str], None] = lambda _: None
    heartbeats: list[str] = field(default_factory=list)


_install_orchestrator_orchestrator_1(globals())
_install_orchestrator_orchestrator_2(globals())
_install_orchestrator_orchestrator_3(globals())
_install_orchestrator_orchestrator_4(globals())
_install_orchestrator_orchestrator_5(globals())
_install_orchestrator_orchestrator_6(globals())
