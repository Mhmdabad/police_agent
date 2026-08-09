"""The search sees what one ply cannot, and never breaks what the match needs.

The shipped brain ranks the five candidates one ply deep. That is sound and it
is blind to a manoeuvre that takes two: the roomy cell it prefers can be the
mouth of a corridor the cop seals next turn. These tests pin the three things
that make a search safe to put in a graded, audited, replayable match — it
finds the win, it refuses the trap, and it is deterministic — and then the one
thing that makes it worth having, which is that it beats the heuristic.
"""

from dataclasses import replace

from cop_agent.domain.actions import MoveAction, PlaceBarrier
from cop_agent.domain.axes import AxisConvention
from cop_agent.domain.board import BoardState
from cop_agent.domain.lookahead import WIN, Search, captured
from cop_agent.domain.lookahead_eval import evaluate
from cop_agent.domain.lookahead_moves import candidates, sealable
from cop_agent.domain.scenarios import blend, likeliest
from cop_agent.strategy.police_brain import PoliceBrain
from cop_agent.strategy.police_search import SearchingPolice

AXES = AxisConvention()
CONTEXT: dict[str, object] = {"threat": 0.5, "concentration": 0.5, "uncertainty": 0.5}


def board(**changes: object) -> BoardState:
    base = BoardState(grid_size=8, cop=(0, 0), thief=(4, 4), barriers=frozenset(), step=0)
    return replace(base, **changes)  # type: ignore[arg-type]


def engine(depth: int = 4) -> Search:
    return Search(
        axes=AXES,
        evaluate=lambda state, turn: evaluate(state, AXES, turn),
        actions=lambda state, agent: candidates(state, agent, AXES, 14),
        depth=depth,
    )


class TestItFindsTheWin:
    def test_the_cop_seals_the_thief_when_sealing_wins(self) -> None:
        """Rule 46: a barrier on the thief's cell is a capture."""
        state = board(cop=(4, 5), thief=(4, 4))
        chosen = engine().best(state, "cop")
        assert chosen == PlaceBarrier(at=(4, 4))

    def test_a_capture_outscores_every_heuristic_sum(self) -> None:
        """WIN has to dominate, or the engine trades a win for a rounding error."""
        state = board(cop=(4, 5), thief=(4, 4))
        assert engine().value_of(state, "cop", PlaceBarrier(at=(4, 4))) >= WIN


class TestItRefusesTheTrap:
    def test_it_prefers_the_cell_with_more_ways_out(self) -> None:
        """Degree is what keeps a thief alive; a corner is where it dies.

        Stated as a preference over the resulting cell rather than as a named
        move, so the test says what the evaluation is for instead of encoding
        one hand-built board's answer.
        """
        from cop_agent.domain.rules import legal_moves, target_of

        state = board(cop=(4, 4), thief=(0, 1))
        chosen = engine().best(state, "thief")
        assert isinstance(chosen, MoveAction)
        landed = target_of((0, 1), chosen.move, AXES)
        corner_exits = len(legal_moves(replace(state, thief=(0, 0)), "thief", AXES))
        assert len(legal_moves(replace(state, thief=landed), "thief", AXES)) >= corner_exits


class TestItIsDeterministic:
    def test_the_same_board_always_returns_the_same_action(self) -> None:
        """A match that cannot be replayed cannot be audited."""
        state = board(cop=(2, 3), thief=(5, 5))
        assert [engine().best(state, "thief") for _ in range(5)].count(
            engine().best(state, "thief")
        ) == 5

    def test_the_brain_never_draws_from_the_policys_stream(self) -> None:
        brain = SearchingPolice(axes=AXES, seed=5)
        before = brain.rng.getstate()
        brain.decide(board(), **CONTEXT)
        assert brain.rng.getstate() == before

    def test_two_brains_with_one_seed_agree(self) -> None:
        state = board(cop=(1, 6), thief=(6, 1))
        first = SearchingPolice(axes=AXES, seed=2).decide(state, **CONTEXT)
        second = SearchingPolice(axes=AXES, seed=2).decide(state, **CONTEXT)
        assert first.action == second.action


class TestItOnlyEverOffersLegalActions:
    def test_barriers_stay_within_the_cops_reach(self) -> None:
        """Placement is the cop's own cell or an orthogonal neighbour."""
        state = board(cop=(3, 3))
        for cell in sealable(state, AXES):
            assert abs(cell[0] - 3) + abs(cell[1] - 3) <= 1

    def test_a_spent_quota_offers_no_placements(self) -> None:
        """Planning around barriers we cannot place is planning a fantasy."""
        walls = frozenset({(7, 7), (7, 6), (6, 7)})
        state = board(barriers=walls)
        assert not [
            action
            for action in candidates(state, "cop", AXES, len(walls))
            if isinstance(action, PlaceBarrier)
        ]

    def test_the_thief_is_never_offered_a_barrier(self) -> None:
        assert all(
            not isinstance(action, PlaceBarrier)
            for action in candidates(board(), "thief", AXES, 14)
        )


class TestTheBeliefLayer:
    def test_sealed_cells_are_not_worth_a_hypothesis(self) -> None:
        """No piece stands on a barrier; mass sitting there is stale."""
        state = board(barriers=frozenset({(1, 1)}))
        assert (1, 1) not in dict(likeliest({(1, 1): 0.9, (2, 2): 0.1}, state))

    def test_weights_are_renormalised_over_what_survives(self) -> None:
        picked = likeliest({(1, 1): 0.2, (2, 2): 0.2, (3, 3): 0.2}, board(), limit=2)
        assert abs(sum(weight for _, weight in picked) - 1.0) < 1e-9

    def test_the_worst_case_pulls_the_blend_below_the_mean(self) -> None:
        """A line that is fine four times and fatal once is not a fine line."""
        assert blend([(10.0, 0.8), (-100.0, 0.2)]) < 10.0 * 0.8 + -100.0 * 0.2 + 1e-9

    def test_an_empty_belief_prefers_nothing(self) -> None:
        assert blend([]) == 0.0


class TestItBeatsTheHeuristic:
    def test_it_contains_the_thief_better_than_the_shipped_brain(self) -> None:
        """The measurement the change is justified by, kept as a regression.

        Capture is the wrong yardstick here: on an open board with this step
        threshold a competent thief is rarely caught by anyone, so a capture
        count is mostly zeroes and discriminates nothing. Containment is what
        the cop actually buys — the free cells the thief can still reach when
        the clock runs out — and it is what converts on a smaller board or a
        weaker opponent.
        """
        from cop_agent.domain.rules import advance_turn
        from cop_agent.domain.search import reachable_area
        from cop_agent.domain.turn_order import advance_both

        def escape_area(brain: PoliceBrain, start: BoardState) -> int:
            state, quarry = start, engine(depth=3)
            for _ in range(35):
                state = advance_turn(state)
                ours = brain.decide(state, **CONTEXT).action
                theirs = quarry.best(state, "thief") or MoveAction("STAY")
                state = advance_both(state, "cop", ours, theirs, AXES, "thief")
                if captured(state, AXES):
                    return 0
            return reachable_area(state, state.thief, AXES)

        openings = [
            board(cop=(0, 0), thief=(3, 3)),
            board(cop=(7, 7), thief=(5, 5)),
            board(cop=(3, 4), thief=(6, 2)),
        ]
        searched = sum(escape_area(SearchingPolice(axes=AXES), s) for s in openings)
        heuristic = sum(escape_area(PoliceBrain(axes=AXES), s) for s in openings)
        assert searched < heuristic, f"search left {searched} cells vs heuristic {heuristic}"
