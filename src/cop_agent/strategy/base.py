"""The strategy module's contract.

This is where the grade lives. Everything else in the repository is
infrastructure both teams must build identically from the same rulebook; the
brain is the only place one agent can out-think another.

It plugs into the runtime at exactly one point — **after the incoming hint is
decoded, before the outgoing Commit is packed** — and everything between those
two points is the agent's intelligence: belief update, action choice, and the
deception text.

**The move is always chosen here, in Python.** Language models hallucinate in
Cartesian space: they confuse directions, distances and coordinates, and will
return an illegal or self-destructive action with complete confidence. The
model writes text and profiles the opponent's language; the algorithm owns
every spatial decision.

Two overrides exist because the cop has two kinds of turn. ``_pick_move``
chooses a relocation; ``_decide_move`` chooses between relocating and
forfeiting movement to place a barrier. A thief brain needs only the first.
"""

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from ..domain.actions import (
    DEFAULT_MAX_BARRIERS,
    Action,
    IllegalActionError,
    MoveAction,
    PlaceBarrier,
    place_barrier,
)
from ..domain.axes import AxisConvention
from ..domain.board import Agent, BoardState, Move
from ..domain.rules import legal_moves


class NoLegalActionError(RuntimeError):
    """Raised when a brain is asked to act with nothing legal available.

    Not the same as being enclosed: a thief with no legal move is captured,
    which is a terminal state the runtime should have detected before asking
    for an action. Reaching here means the caller skipped that check.
    """


class StrategyContextError(TypeError):
    """A configured brain cannot accept the documented belief context."""


@dataclass
class Decision:
    """One turn's output: what to do, and what to say about it."""

    action: Action
    hint: str = ""
    intent: str = "truth"
    reasoning: str = ""


@dataclass
class BrainBase(ABC):
    """Base for a peer's decision-making.

    Subclasses override :meth:`_pick_move`, and the cop additionally overrides
    :meth:`_decide_move` to choose barrier placements.

    Randomness is seeded and the seed recorded. Identical state plus identical
    config must yield an identical action, or a match cannot be replayed and a
    reported bug cannot be reproduced — both of which the audit depends on.
    """

    axes: AxisConvention = field(default_factory=AxisConvention)
    seed: int = 0
    max_barriers: int = DEFAULT_MAX_BARRIERS
    rng: random.Random = field(init=False)

    def __post_init__(self) -> None:
        self.rng = random.Random(self.seed)

    @property
    @abstractmethod
    def role(self) -> Agent:
        """Which side this brain plays."""

    def decide(self, state: BoardState, **context: object) -> Decision:
        """Choose this turn's action.

        The single entry point the runtime calls, positioned after hint decode
        and before Commit packing. Subclasses override the hooks below rather
        than this method, so the legality guard cannot be bypassed.

        At runtime ``state.thief`` is the belief peak, not private truth, and
        ``context`` contains stable ``target``, ``concentration``, and
        ``uncertainty`` keys. Configured brains should accept ``**context``.

        Raises:
            NoLegalActionError: if nothing legal is available.
        """
        action = self._decide_move(state, **context)
        self._guard(state, action)
        return Decision(action=action, hint=self._hint(state, action, **context))

    def _hint(self, state: BoardState, action: Action, **context: object) -> str:
        """Supply one deterministic safe verbal hint for this accepted turn.

        Custom brains may override this hook, or override :meth:`decide` and
        return a complete :class:`Decision`.  The default remains deliberately
        vague: it is valid for moves, barriers, and ``STAY`` and discloses no
        coordinate or future action.
        """
        del state, action, context
        return "I am watching the streets"

    def _decide_move(self, state: BoardState, **context: object) -> Action:
        """Choose between relocating and any role-specific alternative.

        The default is to relocate. The cop overrides this to weigh a barrier
        placement against a move; the thief has no alternative and inherits it.
        """
        return MoveAction(self._pick_move(state, **context))

    @abstractmethod
    def _pick_move(self, state: BoardState, **context: object) -> Move:
        """Choose a relocation. This is the method a strategy overrides."""

    def options(self, state: BoardState) -> list[Move]:
        """Legal moves for this brain's role, in stable order."""
        return legal_moves(state, self.role, self.axes)

    def _guard(self, state: BoardState, action: Action) -> None:
        """Re-validate whatever a subclass produced.

        Defence in depth. Even a heuristic — or a model suggestion, under the
        mutually agreed exception — can produce something illegal, and catching
        it here costs a local error rather than a rejected move and a technical
        loss.

        Both kinds of turn are checked, because the cop has two. A placement
        is validated by *attempting* it against :func:`~..domain.actions.
        place_barrier` and discarding the result, rather than by restating
        reach, occupancy and quota here. Restating them would mean two
        definitions of a legal placement that agree until one is edited — and
        the one that decides the match is the opponent's copy of the rules,
        not ours.

        Raises:
            NoLegalActionError: if the action is not legal in this state.
        """
        if isinstance(action, PlaceBarrier):
            try:
                place_barrier(state, action.at, self.axes, self.max_barriers)
            except IllegalActionError as exc:
                raise NoLegalActionError(f"{self.role} chose an illegal barrier: {exc}") from exc
            return
        available = self.options(state)
        if not available:
            raise NoLegalActionError(f"{self.role} has no legal move")
        if action.move not in available:
            raise NoLegalActionError(
                f"{self.role} chose {action.move}, which is not among {available}"
            )
