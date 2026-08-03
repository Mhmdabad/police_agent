"""The cop's decision-making.

Pursue the target by Manhattan distance, breaking ties by **containment
value** rather than by position.

Distance alone decides where to step but not which of several equally close
steps is worth taking, and those are not equivalent. The rulebook's real
objective for this agent is not *chase the thief* but *shrink the space the
thief has*: enclosure costs two barriers in a corner, three on an edge and
four in open board, so herding matters more than closing.

The tie-break scores a candidate by how much it reduces the thief's reachable
area, falling back to proximity to the board edge when reachability cannot
separate them. Both are cheap and both point the pursuit the same way.
"""

from dataclasses import dataclass, replace

from ..domain.board import MOVES, Agent, BoardState, Move, Position
from ..domain.rules import target_of
from ..domain.search import reachable_area
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
        return min(available, key=lambda move: self._rank(state, move, goal))

    def _rank(self, state: BoardState, move: Move, goal: Position) -> tuple[int, int, int, int]:
        """Order candidates: distance first, then containment value.

        Returned as a tuple so ``min`` applies the criteria in priority order
        and the final element keeps the ordering total — two candidates that
        tie on everything else resolve by :data:`~..domain.board.MOVES` index,
        which is stable across peers and therefore replay-safe.
        """
        destination = target_of(state.cop, move, self.axes)
        distance = manhattan(destination, goal)
        after = replace(state, cop=destination)
        escape = reachable_area(after, goal, self.axes)
        edge = self._edge_pressure(state, goal)
        return (distance, escape, edge, MOVES.index(move))

    def _edge_pressure(self, state: BoardState, goal: Position) -> int:
        """How far the target sits from the nearest board edge.

        Lower is better for us: a target near an edge is one enclosure can
        close with two or three barriers instead of four. Used only when
        reachability cannot separate two candidates, which on an open board is
        most of the time.
        """
        row, col = goal
        last = state.grid_size - 1
        return min(row, col, last - row, last - col)
