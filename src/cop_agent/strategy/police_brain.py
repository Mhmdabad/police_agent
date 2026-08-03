"""The cop's decision-making.

A first, deliberately transparent policy: pursue the target by Manhattan
distance, and never relocate somewhere illegal. The refinements the rulebook's
strategy chapter calls for — containment scoring, the self-preservation veto,
the barrier budget curve — arrive as separate changes on top of this.

Starting plain is the point. The rulebook treats pure heuristics as a
first-class route, competitive with reinforcement learning, and a policy that
can be read in one sitting is one whose mistakes can be found.
"""

from dataclasses import dataclass

from ..domain.board import Agent, BoardState, Move, Position
from ..domain.rules import target_of
from .base import BrainBase, NoLegalActionError


def manhattan(a: Position, b: Position) -> int:
    """Steps between two cells, ignoring barriers.

    Admissible for orthogonal movement with no diagonals: it never
    overestimates, because every step changes exactly one coordinate by one.
    """
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


@dataclass
class PoliceBrain(BrainBase):
    """Pursues the highest-belief cell by minimising Manhattan distance."""

    @property
    def role(self) -> Agent:
        return "cop"

    def target(self, state: BoardState, **context: object) -> Position:
        """The cell to pursue.

        Until the belief map exists this is the thief's actual position, which
        is the "blind" stage the build order calls for: prove the decision core
        is right under full information before adding uncertainty on top.
        """
        supplied = context.get("target")
        if isinstance(supplied, tuple) and len(supplied) == 2:
            return (int(supplied[0]), int(supplied[1]))
        return state.thief

    def _pick_move(self, state: BoardState, **context: object) -> Move:
        """The legal move that gets closest to the target.

        Ties are broken by :data:`~..domain.board.MOVES` order rather than
        randomly, so two peers replaying the same match reach the same move.
        Better tie-breaking — containment value — is a later refinement, and
        this ordering is what it will replace.

        Raises:
            NoLegalActionError: if no move is legal.
        """
        available = self.options(state)
        if not available:
            raise NoLegalActionError("cop has no legal move")
        goal = self.target(state, **context)
        return min(
            available, key=lambda move: manhattan(target_of(state.cop, move, self.axes), goal)
        )
