"""Tests for the barrier spending curve and endgame reserve (#44)."""

import pytest

from cop_agent.domain.actions import DEFAULT_MAX_BARRIERS
from cop_agent.domain.axes import AxisConvention
from cop_agent.domain.board import BoardState
from cop_agent.domain.search import reachable_area
from cop_agent.strategy.budget import (
    DIFFUSE_DEMAND,
    ENDGAME_AREA,
    RESERVE,
    Budget,
    looks_like_endgame,
    worth_spending,
)

AXES = AxisConvention()


def board(**kw: object) -> BoardState:
    cop = kw.get("cop", (0, 0))
    thief = kw.get("thief", (3, 3))
    barriers = kw.get("barriers", frozenset())
    assert isinstance(cop, tuple) and isinstance(thief, tuple)
    assert isinstance(barriers, frozenset | set)
    return BoardState(cop=cop, thief=thief, grid_size=7, barriers=frozenset(barriers))


class TestQuota:
    def test_the_default_limit_is_the_appendix_f_value(self) -> None:
        assert Budget(used=0).limit == DEFAULT_MAX_BARRIERS == 14

    def test_remaining_counts_down(self) -> None:
        assert Budget(used=5).remaining == 9

    def test_it_never_reports_a_negative_remainder(self) -> None:
        """A raised quota is legal; a lowered one is not, but the arithmetic
        should not produce nonsense if the count is ever wrong."""
        assert Budget(used=20).remaining == 0
        assert Budget(used=20).spendable == 0

    def test_spendable_excludes_the_reserve(self) -> None:
        assert Budget(used=0).spendable == 14 - RESERVE


class TestReserve:
    def test_the_reserve_is_the_price_of_an_edge_enclosure(self) -> None:
        """Two only suffices in a corner. A reserve sized for the cheapest
        case runs out in every other one."""
        assert RESERVE == 3

    def test_spending_stops_while_barriers_remain(self) -> None:
        """The whole point: the cop stops placing while it still has some."""
        budget = Budget(used=DEFAULT_MAX_BARRIERS - RESERVE)
        assert budget.remaining == RESERVE
        assert not budget.may_spend(endgame=False)

    def test_the_endgame_unlocks_it(self) -> None:
        budget = Budget(used=DEFAULT_MAX_BARRIERS - RESERVE)
        assert budget.may_spend(endgame=True)

    def test_an_exhausted_quota_stays_exhausted_in_the_endgame(self) -> None:
        assert not Budget(used=DEFAULT_MAX_BARRIERS).may_spend(endgame=True)

    def test_the_last_barrier_outside_the_reserve_is_spendable(self) -> None:
        budget = Budget(used=DEFAULT_MAX_BARRIERS - RESERVE - 1)
        assert budget.spendable == 1
        assert budget.may_spend(endgame=False)

    @pytest.mark.parametrize("used", range(DEFAULT_MAX_BARRIERS + 1))
    def test_the_reserve_is_never_breached_before_the_endgame(self, used: int) -> None:
        """#44's acceptance criterion, swept across the whole quota."""
        budget = Budget(used=used)
        if budget.may_spend(endgame=False):
            assert budget.remaining > RESERVE


class TestSpendRate:
    def test_diffuse_belief_demands_a_corridor(self) -> None:
        assert Budget(used=0).required_value(0.0) == DIFFUSE_DEMAND

    def test_concentrated_belief_demands_almost_nothing(self) -> None:
        assert Budget(used=0).required_value(1.0) == 1

    def test_it_never_demands_zero(self) -> None:
        """A barrier reducing nothing is never worth spending, however sure
        we are about where the thief is."""
        assert Budget(used=0).required_value(1.0) >= 1

    def test_the_demand_falls_as_belief_sharpens(self) -> None:
        budget = Budget(used=0)
        demands = [budget.required_value(c / 10) for c in range(11)]
        assert demands == sorted(demands, reverse=True)

    def test_out_of_range_concentration_is_clamped_not_trusted(self) -> None:
        """A belief map with a normalisation bug should not buy free barriers."""
        budget = Budget(used=0)
        assert budget.required_value(-5.0) == DIFFUSE_DEMAND
        assert budget.required_value(5.0) == 1


class TestEndgameDetection:
    def test_an_open_board_is_not_an_endgame(self) -> None:
        assert not looks_like_endgame(board(), AXES, (3, 3))

    def test_a_small_pocket_is(self) -> None:
        walls = {(0, 2), (1, 2), (2, 2), (2, 1), (2, 0)}
        state = board(thief=(0, 0), barriers=walls)
        assert looks_like_endgame(state, AXES, (0, 0))

    def test_it_is_measured_in_room_not_in_turns(self) -> None:
        """A clock-based unlock hands the reserve over on turn thirty with the
        thief loose in open board — the exact case it was withheld for."""
        late = BoardState(cop=(0, 0), thief=(3, 3), grid_size=7, step=30)
        assert not looks_like_endgame(late, AXES, (3, 3))

    def test_the_threshold_is_a_boundary_not_a_direction(self) -> None:
        """A pocket of exactly ENDGAME_AREA unlocks; one cell more does not."""
        eight = {(0, 4), (1, 4)} | {(2, col) for col in range(4)}
        exact = board(thief=(0, 0), barriers=eight)
        assert reachable_area(exact, (0, 0), AXES) == ENDGAME_AREA
        assert looks_like_endgame(exact, AXES, (0, 0))

        nine = {(0, 3), (1, 3), (2, 3)} | {(3, col) for col in range(3)}
        over = board(thief=(0, 0), barriers=nine)
        assert reachable_area(over, (0, 0), AXES) == ENDGAME_AREA + 1
        assert not looks_like_endgame(over, AXES, (0, 0))


class TestWorthSpending:
    def test_a_good_placement_against_sharp_belief_is_spent(self) -> None:
        assert worth_spending(3, Budget(used=0), concentration=1.0, endgame=False)

    def test_the_same_placement_against_diffuse_belief_is_not(self) -> None:
        assert not worth_spending(3, Budget(used=0), concentration=0.0, endgame=False)

    def test_the_reserve_overrides_a_good_placement(self) -> None:
        """Value cannot buy a reserved barrier. That is what reserving means."""
        budget = Budget(used=DEFAULT_MAX_BARRIERS - RESERVE)
        assert not worth_spending(40, budget, concentration=1.0, endgame=False)
        assert worth_spending(40, budget, concentration=1.0, endgame=True)

    def test_a_worthless_placement_is_refused_even_in_the_endgame(self) -> None:
        assert not worth_spending(0, Budget(used=13), concentration=1.0, endgame=True)


class TestReporting:
    def test_the_split_is_legible(self) -> None:
        assert str(Budget(used=4)) == "budget: 4/14 used, 7 free + 3 reserved"

    def test_it_does_not_report_a_reserve_it_no_longer_has(self) -> None:
        assert str(Budget(used=13)) == "budget: 13/14 used, 0 free + 1 reserved"
