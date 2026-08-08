"""Tests for the movement-forfeit cost comparison (#46)."""

import logging

import pytest

from cop_agent.domain.actions import DEFAULT_MAX_BARRIERS, MoveAction, PlaceBarrier
from cop_agent.domain.axes import AxisConvention
from cop_agent.domain.board import BoardState
from cop_agent.strategy.barriers import BarrierScore
from cop_agent.strategy.budget import RESERVE, Budget
from cop_agent.strategy.police_brain import PoliceBrain
from cop_agent.strategy.tradeoff import Tradeoff, distance_closed, weigh

AXES = AxisConvention()
CORRIDOR = frozenset({(0, 2), (1, 2), (3, 2), (4, 2), (5, 2), (6, 2)})


def board(**kw: object) -> BoardState:
    cop = kw.get("cop", (0, 0))
    thief = kw.get("thief", (3, 3))
    barriers = kw.get("barriers", frozenset())
    assert isinstance(cop, tuple) and isinstance(thief, tuple)
    assert isinstance(barriers, frozenset | set)
    return BoardState(cop=cop, thief=thief, grid_size=7, barriers=frozenset(barriers))


GOOD_PLACEMENT = BarrierScore(at=(1, 1), escape_reduction=5, chain=0, disconnects=False)


def call(
    placement: BarrierScore | None = GOOD_PLACEMENT,
    move_gain: int = 1,
    required: int = 1,
    used: int = 0,
    endgame: bool = False,
) -> Tradeoff:
    return Tradeoff(
        placement=placement,
        move_gain=move_gain,
        required=required,
        budget=Budget(used=used),
        endgame=endgame,
    )


class TestDistanceClosed:
    def test_a_step_toward_the_target_closes_one(self) -> None:
        assert distance_closed(board(cop=(0, 0)), "S", (3, 3), AXES) == 1

    def test_standing_still_closes_nothing(self) -> None:
        assert distance_closed(board(cop=(0, 0)), "STAY", (3, 3), AXES) == 0

    def test_a_step_away_is_reported_as_a_loss(self) -> None:
        """Clamping to zero would convert a bad turn into a neutral one and
        let a weak placement through on the difference."""
        assert distance_closed(board(cop=(1, 1)), "N", (3, 3), AXES) == -1


class TestTheComparison:
    def test_a_bigger_cut_than_the_step_is_taken(self) -> None:
        assert call(placement=BarrierScore((1, 1), 5, 0, False), move_gain=1).place

    def test_an_equal_trade_goes_to_the_move(self) -> None:
        """A tie keeps the barrier, and a barrier kept can still be spent."""
        assert not call(placement=BarrierScore((1, 1), 1, 0, False), move_gain=1).place

    def test_a_smaller_cut_is_refused(self) -> None:
        assert not call(placement=BarrierScore((1, 1), 1, 0, False), move_gain=2).place

    def test_the_budget_bar_applies_on_top(self) -> None:
        """Beating the move is necessary, not sufficient: a diffuse belief
        still demands a corridor."""
        beats_the_move = call(placement=BarrierScore((1, 1), 2, 0, False), move_gain=1)
        assert beats_the_move.place
        assert not call(placement=BarrierScore((1, 1), 2, 0, False), move_gain=1, required=6).place

    def test_no_permitted_placement_means_move(self) -> None:
        assert not call(placement=None).place

    def test_the_reserve_refuses_however_good_the_trade(self) -> None:
        held = call(
            placement=BarrierScore((1, 1), 40, 0, False),
            move_gain=1,
            used=DEFAULT_MAX_BARRIERS - RESERVE,
        )
        assert not held.affordable
        assert not held.place

    def test_the_endgame_releases_it(self) -> None:
        released = call(
            placement=BarrierScore((1, 1), 40, 0, False),
            move_gain=1,
            used=DEFAULT_MAX_BARRIERS - RESERVE,
            endgame=True,
        )
        assert released.place


class TestBothSidesAreLogged:
    def test_the_figures_that_justified_it_are_in_the_transcript(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """#46's acceptance criterion, verbatim."""
        state = board(cop=(2, 1), thief=(2, 5), barriers=CORRIDOR)
        with caplog.at_level(logging.INFO, logger="cop_agent.strategy.tradeoff"):
            weigh(state, AXES, (2, 5), "E")
        assert "PLACE" in caplog.text
        assert "removes 14" in caplog.text
        assert "vs move closing 1" in caplog.text
        assert "budget:" in caplog.text

    def test_a_refusal_is_logged_just_as_loudly(self, caplog: pytest.LogCaptureFixture) -> None:
        """A transcript that only records the placements taken cannot explain
        the ones declined."""
        with caplog.at_level(logging.INFO, logger="cop_agent.strategy.tradeoff"):
            weigh(board(cop=(0, 0), thief=(3, 3)), AXES, (3, 3), "S")
        assert "MOVE" in caplog.text

    def test_the_endgame_is_marked(self, caplog: pytest.LogCaptureFixture) -> None:
        pocket = {(0, 4), (1, 4)} | {(2, col) for col in range(4)}
        state = board(cop=(0, 3), thief=(0, 0), barriers=pocket)
        with caplog.at_level(logging.INFO, logger="cop_agent.strategy.tradeoff"):
            weigh(state, AXES, (0, 0), "W")
        assert "endgame" in caplog.text


class TestOpenBoardRefusesByDefault:
    def test_a_barrier_on_open_ground_never_beats_the_step(self) -> None:
        """The intended reading: barriers are for corridors and corners."""
        for cop in ((0, 0), (1, 1), (2, 2), (3, 4), (5, 1)):
            state = board(cop=cop, thief=(3, 3))
            move = PoliceBrain(axes=AXES)._pick_move(state, target=state.thief)
            assert not weigh(state, AXES, (3, 3), move).place

    def test_so_the_cop_moves(self) -> None:
        state = board(cop=(0, 0), thief=(3, 3))
        action = PoliceBrain(axes=AXES).decide(state, target=state.thief).action
        assert isinstance(action, MoveAction)


class TestTheBrainWiresItTogether:
    def test_a_win_skips_the_comparison_entirely(self) -> None:
        """Neither escape area nor the budget matters once the match is over."""
        walls = {(6, col) for col in range(7)} | {(5, col) for col in range(5)}
        state = board(cop=(3, 3), thief=(3, 4), barriers=walls)
        assert Budget(used=state.barriers_used).spendable == 0
        assert PoliceBrain(axes=AXES).decide(state, target=state.thief).action == PlaceBarrier(
            (3, 4)
        )

    def test_an_illegal_move_is_caught_before_it_is_weighed(self) -> None:
        """Otherwise the comparison consumes a distance to a cell that is not
        on the board, and choosing to place would swallow the bug silently.
        """

        class Rogue(PoliceBrain):
            def _pick_move(self, state: BoardState, **context: object) -> str:  # type: ignore[override]
                return "N"

        with pytest.raises(Exception, match="not among"):
            state = board(cop=(0, 0), thief=(3, 3))
            Rogue(axes=AXES).decide(state, target=state.thief)

    def test_concentration_defaults_to_the_uninformative_prior(self) -> None:
        assert PoliceBrain(axes=AXES).concentration() == 0.0

    def test_a_supplied_concentration_is_used(self) -> None:
        assert PoliceBrain(axes=AXES).concentration(concentration=0.25) == 0.25

    def test_a_nonsense_concentration_falls_back_rather_than_crashing(self) -> None:
        assert PoliceBrain(axes=AXES).concentration(concentration="soon") == 0.0


class TestTheNegotiatedQuotaIsHonoured:
    """The quota is an Appendix F *minimum*, so it varies between matches."""

    def test_the_policy_budgets_against_the_brains_limit_not_the_book(self) -> None:
        """Found by a determinism test, not by a strategy one.

        The comparison used to build its Budget from the book value while the
        guard enforced the brain's configured quota. With six barriers down
        and a negotiated limit of six, the policy proposed a placement and the
        guard refused it — a crash on the cop's own turn rather than a
        decision, and a technical loss worth zero to both sides.
        """
        state = board(cop=(2, 1), thief=(2, 5), barriers=CORRIDOR)
        assert state.barriers_used == 6
        assert weigh(state, AXES, (2, 5), "E", max_barriers=14).place
        assert not weigh(state, AXES, (2, 5), "E", max_barriers=6).place

    def test_the_brain_falls_through_to_moving(self) -> None:
        state = board(cop=(2, 1), thief=(2, 5), barriers=CORRIDOR)
        assert isinstance(
            PoliceBrain(axes=AXES).decide(state, target=state.thief).action, PlaceBarrier
        )
        spent = PoliceBrain(axes=AXES, max_barriers=6).decide(state, target=state.thief).action
        assert isinstance(spent, MoveAction)

    def test_a_raised_quota_is_spendable_once_it_clears_the_reserve(self) -> None:
        """Raising it by agreement is legal; the policy must notice — and the
        reserve rides on the negotiated limit rather than the book one, so the
        boundary moves with it."""
        walls = CORRIDOR | {(6, col) for col in range(4)}
        state = board(cop=(2, 1), thief=(2, 5), barriers=walls)
        assert state.barriers_used == 9
        assert not weigh(state, AXES, (2, 5), "E", max_barriers=12).place
        assert weigh(state, AXES, (2, 5), "E", max_barriers=13).place
        assert Budget(used=9, limit=12).spendable == 0
        assert Budget(used=9, limit=13).spendable == 1

    def test_a_win_respects_it_too(self) -> None:
        walls = frozenset({(6, col) for col in range(7)})
        state = board(cop=(3, 3), thief=(3, 4), barriers=walls)
        assert PoliceBrain(axes=AXES).decide(state, target=state.thief).action == PlaceBarrier(
            (3, 4)
        )
        assert isinstance(
            PoliceBrain(axes=AXES, max_barriers=7).decide(state, target=state.thief).action,
            MoveAction,
        )
