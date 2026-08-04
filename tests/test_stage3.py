"""Stage 3 acceptance tests (#50).

Four criteria, gathered here rather than left scattered through the suites
that produced each piece, so the stage can be read in one place.

The determinism criterion is covered in depth in ``test_determinism.py``
(#48) — across processes under four hash seeds, across a whole match, and
with the RNG stream asserted untouched. What is here is the criterion stated
plainly, so #50 is answered without duplicating that file.
"""

import random
from dataclasses import replace

import pytest

from cop_agent.domain.actions import (
    DEFAULT_MAX_BARRIERS,
    MoveAction,
    PlaceBarrier,
    apply_action,
    placement_range,
)
from cop_agent.domain.axes import AxisConvention
from cop_agent.domain.board import MOVES, BoardState
from cop_agent.domain.outcome import is_capture_by_overlap, is_trapping_capture
from cop_agent.domain.rules import legal_moves, target_of
from cop_agent.domain.scoring import Outcome, evaluate
from cop_agent.strategy.barriers import best_placement, rank_placements, safe_placements
from cop_agent.strategy.base import NoLegalActionError
from cop_agent.strategy.budget import RESERVE, Budget, looks_like_endgame
from cop_agent.strategy.police_brain import PoliceBrain

AXES = AxisConvention()


def make(**kw: object) -> BoardState:
    cop = kw.get("cop", (0, 0))
    thief = kw.get("thief", (3, 3))
    barriers = kw.get("barriers", frozenset())
    step = kw.get("step", 0)
    assert isinstance(cop, tuple) and isinstance(thief, tuple)
    assert isinstance(barriers, frozenset | set) and isinstance(step, int)
    return BoardState(cop=cop, thief=thief, grid_size=7, barriers=frozenset(barriers), step=step)


def evade(state: BoardState) -> BoardState:
    """Move the thief away from the cop, greedily.

    Deliberately the naive distance-maximising policy rather than our own
    thief's — a stationary thief is captured in six turns and exercises almost
    nothing, and importing the opponent's brain is not available to us anyway.
    Ties break by ``MOVES`` order so the match stays reproducible.
    """
    options = legal_moves(state, "thief", AXES)
    if not options:
        return state
    best = max(
        options,
        key=lambda move: (
            abs(target_of(state.thief, move, AXES)[0] - state.cop[0])
            + abs(target_of(state.thief, move, AXES)[1] - state.cop[1]),
            -MOVES.index(move),
        ),
    )
    return replace(state, thief=target_of(state.thief, best, AXES))


class TestNeverIllegal:
    """#50, first criterion: over randomly generated boards."""

    def test_the_policy_output_is_always_legal(self) -> None:
        """#47's property test forces actions into the guard, which is the
        backstop. This one asks the *policy* what it produces."""
        rng = random.Random(50)
        cells = [(row, col) for row in range(7) for col in range(7)]
        moved = placed = 0
        for _ in range(400):
            walls = frozenset(rng.sample(cells, rng.randint(0, 13)))
            free = [cell for cell in cells if cell not in walls]
            if len(free) < 2:
                continue
            state = make(cop=rng.choice(free), thief=rng.choice(free), barriers=walls)
            if is_capture_by_overlap(state) or is_trapping_capture(state):
                continue
            if not legal_moves(state, "cop", AXES):
                with pytest.raises(NoLegalActionError):
                    PoliceBrain(axes=AXES).decide(state)
                continue
            action = PoliceBrain(axes=AXES).decide(state).action
            if isinstance(action, PlaceBarrier):
                assert action.at in placement_range(state, AXES)
                assert not state.is_barrier(action.at)
                placed += 1
            else:
                assert action.move in legal_moves(state, "cop", AXES)
                moved += 1
            apply_action(state, "cop", action, AXES)
        assert moved > 0 and placed > 0, f"moved={moved} placed={placed}"

    def test_a_sealed_in_cop_raises_rather_than_inventing_a_move(self) -> None:
        walls = frozenset({(2, 3), (4, 3), (3, 2), (3, 4), (3, 3)})
        with pytest.raises(NoLegalActionError, match="no legal move"):
            PoliceBrain(axes=AXES).decide(make(cop=(3, 3), thief=(0, 0), barriers=walls))


class TestSelfWallOffRegression:
    """#50, second criterion: the self-preservation constraint holds."""

    def test_a_placement_that_cuts_us_off_is_refused_though_it_scores_better(
        self,
    ) -> None:
        """The regression board.

        Cop at (0, 0) with (1, 0) already sealed. Sealing (0, 1) removes twice
        as much of the thief's escape area as the placement actually chosen —
        and imprisons the cop in a one-cell pocket. A weight could be outvoted
        by a large enough score; a constraint cannot.
        """
        state = make(cop=(0, 0), thief=(2, 2), barriers={(1, 0)})
        ranked = {score.at: score for score in rank_placements(state, AXES, (2, 2))}
        assert ranked[(0, 1)].disconnects
        assert ranked[(0, 1)].escape_reduction > ranked[(0, 0)].escape_reduction
        assert (0, 1) not in {score.at for score in safe_placements(state, AXES, (2, 2))}
        assert PoliceBrain(axes=AXES).decide(state).action != PlaceBarrier((0, 1))

    def test_a_placement_leaving_no_legal_move_is_refused(self) -> None:
        """The more expensive half. An unanswered turn is a technical loss,
        and a technical loss scores zero for *both* sides."""
        state = make(cop=(0, 0), thief=(2, 2), barriers={(0, 1), (1, 0)})
        assert legal_moves(state, "cop", AXES) == ["STAY"]
        only = rank_placements(state, AXES, (2, 2))[0]
        assert only.at == (0, 0) and only.immobilises
        action = PoliceBrain(axes=AXES).decide(state).action
        assert isinstance(action, MoveAction)

    def test_the_cop_never_walls_itself_in_over_a_whole_match(self) -> None:
        """The constraint holding once is not the claim; it has to hold for
        thirty-five turns of its own accumulating barriers."""
        state = make(cop=(0, 0), thief=(6, 6))
        brain = PoliceBrain(axes=AXES)
        for step in range(35):
            if evaluate(state, AXES) is not Outcome.ONGOING:
                break
            assert legal_moves(state, "cop", AXES), f"cop immobilised at step {step}"
            state = apply_action(state, "cop", brain.decide(state).action, AXES)
            state = evade(replace(state, step=step + 1))
        assert legal_moves(state, "cop", AXES)


class TestQuotaNeverExceeded:
    """#50, third criterion.

    Two halves, because the honest answer has two parts. Real matches barely
    spend at all, so playing one out proves the quota holds without ever
    approaching it; the budget therefore also gets a harness that pushes it
    to the limit deliberately.
    """

    def test_a_full_match_stays_within_the_quota(self) -> None:
        state = make(cop=(0, 0), thief=(3, 3))
        brain = PoliceBrain(axes=AXES)
        turns = 0
        for step in range(35):
            if evaluate(state, AXES) is not Outcome.ONGOING:
                break
            state = apply_action(state, "cop", brain.decide(state).action, AXES)
            state = evade(replace(state, step=step + 1))
            turns += 1
            assert state.barriers_used <= DEFAULT_MAX_BARRIERS
        assert turns > 20, f"the match ended after {turns} turns and proved little"

    def test_an_open_board_match_spends_nothing(self) -> None:
        """Not a weakness of the test — the intended reading of #46, verified
        end to end. A barrier on open ground removes one cell while a step
        closes one cell of distance, and a tie goes to the move, so a chase
        across empty board should place nothing at all. Stated here so the
        match test above is not mistaken for a stress test.
        """
        state = make(cop=(0, 0), thief=(3, 3))
        brain = PoliceBrain(axes=AXES)
        placements = 0
        for step in range(35):
            if evaluate(state, AXES) is not Outcome.ONGOING:
                break
            action = brain.decide(state).action
            placements += isinstance(action, PlaceBarrier)
            state = apply_action(state, "cop", action, AXES)
            state = evade(replace(state, step=step + 1))
        assert placements == 0

    def test_a_cop_that_always_places_still_cannot_exceed_the_quota(self) -> None:
        """The stress harness.

        Deliberately not a legal match: it takes a placement *and* a step each
        turn, so the quota is reached in a handful of turns rather than never.
        The property under test belongs to the budget, not to the turn
        structure, and the real policy is too frugal to reach it.
        """
        for limit in (4, 7, 14, 20):
            state = make(cop=(3, 3), thief=(0, 0))
            brain = PoliceBrain(axes=AXES, max_barriers=limit)
            placed = 0
            for _ in range(60):
                budget = Budget(used=state.barriers_used, limit=limit)
                if not budget.may_spend(looks_like_endgame(state, AXES, state.thief)):
                    break
                best = best_placement(state, AXES, state.thief)
                if best is None:
                    break
                state = apply_action(state, "cop", PlaceBarrier(best.at), AXES, max_barriers=limit)
                placed += 1
                assert state.barriers_used <= limit
                options = legal_moves(state, "cop", AXES)
                if not options:
                    break
                state = apply_action(
                    state, "cop", MoveAction(brain._pick_move(state)), AXES, max_barriers=limit
                )
            assert placed > 0, f"limit {limit} never placed anything"
            assert state.barriers_used <= limit

    def test_and_stops_before_breaching_the_reserve(self) -> None:
        """The claim #44 actually makes, which is stronger than the quota."""
        state = make(cop=(3, 3), thief=(0, 0))
        brain = PoliceBrain(axes=AXES)
        for _ in range(60):
            if looks_like_endgame(state, AXES, state.thief):
                return
            if not Budget(used=state.barriers_used).may_spend(endgame=False):
                break
            best = best_placement(state, AXES, state.thief)
            if best is None:
                break
            state = apply_action(state, "cop", PlaceBarrier(best.at), AXES)
            assert state.barriers_used <= DEFAULT_MAX_BARRIERS - RESERVE
            if not legal_moves(state, "cop", AXES):
                break
            state = apply_action(state, "cop", MoveAction(brain._pick_move(state)), AXES)
        assert state.barriers_used == DEFAULT_MAX_BARRIERS - RESERVE

    def test_placement_stops_rather_than_erroring_when_the_quota_runs_out(self) -> None:
        walls = frozenset({(6, col) for col in range(7)})
        state = make(cop=(2, 1), thief=(2, 5), barriers=walls)
        spent = PoliceBrain(axes=AXES, max_barriers=7)
        assert state.barriers_used == 7
        action = spent.decide(state).action
        assert isinstance(action, MoveAction)


class TestDeterminismCriterion:
    """#50, fourth criterion. Depth lives in test_determinism.py."""

    def test_same_state_and_config_yields_the_same_action(self) -> None:
        state = make(cop=(2, 2), thief=(5, 5))
        assert (
            PoliceBrain(axes=AXES, seed=7).decide(state).action
            == PoliceBrain(axes=AXES, seed=7).decide(state).action
        )

    def test_a_whole_match_replays_move_for_move(self) -> None:
        def play(seed: int) -> list[object]:
            state = make(cop=(0, 0), thief=(3, 3))
            brain = PoliceBrain(axes=AXES, seed=seed)
            actions: list[object] = []
            for step in range(20):
                if evaluate(state, AXES) is not Outcome.ONGOING:
                    break
                action = brain.decide(state).action
                actions.append(action)
                state = apply_action(state, "cop", action, AXES)
                state = evade(replace(state, step=step + 1))
            return actions

        assert play(1) == play(2)
        assert len(play(1)) == 20
