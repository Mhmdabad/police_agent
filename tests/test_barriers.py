"""Tests for the barrier value scorer."""

import logging
from dataclasses import replace

import pytest

from cop_agent.domain.axes import AxisConvention
from cop_agent.domain.board import BoardState
from cop_agent.domain.rules import legal_moves
from cop_agent.domain.search import reachable, reachable_area
from cop_agent.strategy.barriers import (
    SELF_PENALTY,
    BarrierScore,
    best_placement,
    chain_progress,
    rank_placements,
    safe_placements,
    score_placement,
)

AXES = AxisConvention()


def board(cop: tuple[int, int], thief: tuple[int, int], **kw: object) -> BoardState:
    barriers = kw.get("barriers", frozenset())
    assert isinstance(barriers, frozenset | set)
    size = kw.get("grid_size", 7)
    assert isinstance(size, int)
    return BoardState(cop=cop, thief=thief, grid_size=size, barriers=frozenset(barriers))


class TestChainProgress:
    def test_open_ground_has_no_closed_sides(self) -> None:
        assert chain_progress(board((3, 3), (5, 5)), (3, 3), AXES) == 0

    def test_a_corner_supplies_two_sides_for_free(self) -> None:
        """Appendix D's two-barrier corner enclosure follows from exactly this."""
        assert chain_progress(board((3, 3), (5, 5)), (0, 0), AXES) == 2

    def test_an_edge_supplies_one(self) -> None:
        assert chain_progress(board((3, 3), (5, 5)), (0, 3), AXES) == 1

    def test_an_existing_barrier_counts_the_same_as_the_edge(self) -> None:
        """A wall lands on either equally well; the scorer must not prefer one."""
        state = board((3, 3), (5, 5), barriers={(2, 2)})
        assert chain_progress(state, (2, 3), AXES) == 1
        assert chain_progress(state, (0, 3), AXES) == 1

    def test_sides_accumulate(self) -> None:
        state = board((3, 3), (5, 5), barriers={(0, 2), (1, 3)})
        assert chain_progress(state, (0, 3), AXES) == 3


class TestEscapeReduction:
    def test_open_board_placement_reduces_by_one(self) -> None:
        """The sealed cell itself leaves the thief's reachable set, nothing more."""
        state = board((3, 3), (5, 5))
        assert score_placement(state, (3, 3), AXES, (5, 5)).escape_reduction == 1

    def test_closing_a_corridor_takes_the_whole_region(self) -> None:
        """Sealing (1, 0) walls the thief into the single cell (0, 0)."""
        state = board((1, 1), (0, 0), grid_size=3, barriers={(0, 1)})
        score = score_placement(state, (1, 0), AXES, (0, 0))
        assert score.escape_reduction == 7
        assert reachable_area(state, (0, 0), AXES) == 8

    def test_a_barrier_the_thief_cannot_reach_costs_it_nothing(self) -> None:
        state = board((2, 2), (0, 0), grid_size=3, barriers={(0, 1), (1, 0)})
        assert score_placement(state, (2, 2), AXES, (0, 0)).escape_reduction == 0


class TestSelfPenalty:
    def test_walling_ourselves_off_is_flagged(self) -> None:
        """The rules permit the cop to imprison itself. A greedy scorer would."""
        state = board((0, 0), (2, 2), grid_size=3, barriers={(1, 0)})
        assert score_placement(state, (0, 1), AXES, (2, 2)).disconnects

    def test_the_penalty_outweighs_any_real_gain(self) -> None:
        """A board has 49 cells; the penalty must dominate a full-board cut."""
        cut = BarrierScore(at=(0, 1), escape_reduction=48, chain=4, disconnects=True)
        assert cut.total < 0
        assert SELF_PENALTY > 49 + 4

    def test_a_placement_that_keeps_the_route_is_not_flagged(self) -> None:
        assert not score_placement(board((3, 3), (5, 5)), (3, 4), AXES, (5, 5)).disconnects

    def test_sealing_our_own_cell_is_not_cutting_ourselves_off(self) -> None:
        """The regression this class exists for.

        ``reachable`` returns the empty set from a sealed origin, so the naive
        check called every self-cell placement a disconnection. The cop is not
        trapped: leaving asks whether the destination is free, so all four
        steps stay legal and only re-entry is lost.
        """
        state = board((3, 3), (5, 5))
        sealed = replace(state, barriers=frozenset({(3, 3)}))
        assert legal_moves(sealed, "cop", AXES) == ["N", "S", "E", "W"]
        assert reachable(sealed, (3, 3), AXES) == frozenset()
        assert not score_placement(state, (3, 3), AXES, (5, 5)).disconnects

    def test_sealing_our_own_cell_in_a_dead_end_does_cut_us_off(self) -> None:
        """The exemption is about re-entry, not a blanket pass."""
        state = board((0, 0), (2, 2), grid_size=3, barriers={(1, 0), (0, 1)})
        assert score_placement(state, (0, 0), AXES, (2, 2)).disconnects


class TestRanking:
    def test_every_reachable_cell_is_a_candidate(self) -> None:
        ranked = rank_placements(board((3, 3), (5, 5)), AXES, (5, 5))
        assert {score.at for score in ranked} == {(3, 3), (2, 3), (4, 3), (3, 2), (3, 4)}

    def test_a_corner_cop_has_three_candidates_not_five(self) -> None:
        ranked = rank_placements(board((0, 0), (5, 5)), AXES, (5, 5))
        assert {score.at for score in ranked} == {(0, 0), (1, 0), (0, 1)}

    def test_already_sealed_cells_are_not_offered(self) -> None:
        state = board((3, 3), (5, 5), barriers={(3, 4)})
        assert (3, 4) not in {score.at for score in rank_placements(state, AXES, (5, 5))}

    def test_best_first(self) -> None:
        ranked = rank_placements(board((0, 1), (2, 2), grid_size=3), AXES, (2, 2))
        assert [score.total for score in ranked] == sorted(
            (score.total for score in ranked), reverse=True
        )

    def test_self_cutting_candidates_sink_to_the_bottom(self) -> None:
        state = board((0, 0), (2, 2), grid_size=3, barriers={(1, 0)})
        ranked = rank_placements(state, AXES, (2, 2))
        assert ranked[-1].disconnects

    def test_ties_resolve_by_position_not_set_order(self) -> None:
        """Reproducible on the opponent's machine, not only on ours."""
        state = board((3, 3), (5, 5))
        first = rank_placements(state, AXES, (5, 5))
        again = rank_placements(replace(state, barriers=frozenset()), AXES, (5, 5))
        assert [score.at for score in first] == [score.at for score in again]

    def test_nothing_available_when_every_reachable_cell_is_sealed(self) -> None:
        state = board((0, 0), (2, 2), grid_size=3, barriers={(0, 0), (0, 1), (1, 0)})
        assert rank_placements(state, AXES, (2, 2)) == []
        assert best_placement(state, AXES, (2, 2)) is None

    def test_best_placement_agrees_with_the_ranking(self) -> None:
        state = board((1, 1), (0, 0), grid_size=3, barriers={(0, 1)})
        assert best_placement(state, AXES, (0, 0)) == rank_placements(state, AXES, (0, 0))[0]


class TestDecisionIsLogged:
    def test_every_candidate_and_its_breakdown_reaches_the_log(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """#42 asks for the output logged on every placement decision: a match
        transcript has to explain why a barrier went where it did."""
        with caplog.at_level(logging.INFO, logger="cop_agent.strategy.barriers"):
            rank_placements(board((3, 3), (5, 5)), AXES, (5, 5))
        assert "escape-" in caplog.text and "chain+" in caplog.text
        assert caplog.text.count("total=") == 5

    def test_an_empty_candidate_set_is_logged_too(self, caplog: pytest.LogCaptureFixture) -> None:
        state = board((0, 0), (2, 2), grid_size=3, barriers={(0, 0), (0, 1), (1, 0)})
        with caplog.at_level(logging.INFO, logger="cop_agent.strategy.barriers"):
            rank_placements(state, AXES, (2, 2))
        assert "every cell in reach is sealed" in caplog.text

    def test_a_self_cutting_candidate_says_so(self, caplog: pytest.LogCaptureFixture) -> None:
        state = board((0, 0), (2, 2), grid_size=3, barriers={(1, 0)})
        with caplog.at_level(logging.INFO, logger="cop_agent.strategy.barriers"):
            rank_placements(state, AXES, (2, 2))
        assert "CUTS-SELF-OFF" in caplog.text


class TestSelfPreservationConstraint:
    """#43: the self term is a hard gate, not a weight."""

    def test_a_placement_that_disconnects_us_from_the_target_is_refused(self) -> None:
        """The regression the issue asks for, stated as it is stated there."""
        state = board((0, 0), (2, 2), grid_size=3, barriers={(1, 0)})
        refused = next(s for s in rank_placements(state, AXES, (2, 2)) if s.at == (0, 1))
        assert refused.disconnects
        assert not refused.permitted
        assert (0, 1) not in {s.at for s in safe_placements(state, AXES, (2, 2))}

    def test_the_refused_placement_was_the_better_looking_one(self) -> None:
        """A weight could be outvoted by a good enough score. A gate cannot."""
        state = board((0, 0), (2, 2), grid_size=3, barriers={(1, 0)})
        refused = next(s for s in rank_placements(state, AXES, (2, 2)) if s.at == (0, 1))
        chosen = best_placement(state, AXES, (2, 2))
        assert chosen is not None and chosen.at == (0, 0)
        assert refused.escape_reduction > chosen.escape_reduction

    def test_a_placement_leaving_no_legal_move_is_refused(self) -> None:
        """The expensive one. An unanswered turn is a technical loss, and a
        technical loss scores zero for *both* sides."""
        state = board((0, 0), (2, 2), grid_size=3, barriers={(0, 1), (1, 0)})
        assert legal_moves(state, "cop", AXES) == ["STAY"]
        only = rank_placements(state, AXES, (2, 2))[0]
        assert only.at == (0, 0)
        assert only.immobilises
        assert not only.permitted

    def test_refusing_everything_means_placing_nothing(self) -> None:
        """``None`` is "do not place", never "place the least bad one"."""
        state = board((0, 0), (2, 2), grid_size=3, barriers={(0, 1), (1, 0)})
        assert rank_placements(state, AXES, (2, 2)) != []
        assert safe_placements(state, AXES, (2, 2)) == []
        assert best_placement(state, AXES, (2, 2)) is None

    def test_immobilising_outranks_disconnecting_in_the_veto_reason(self) -> None:
        """Both true at once reports the one that ends the match sooner."""
        both = BarrierScore(
            at=(0, 0), escape_reduction=9, chain=4, disconnects=True, immobilises=True
        )
        assert both.veto == "NO-LEGAL-MOVE-AFTER"

    def test_a_permitted_placement_has_no_veto_string(self) -> None:
        state = board((3, 3), (5, 5))
        assert all(s.veto == "" and s.permitted for s in safe_placements(state, AXES, (5, 5)))

    def test_the_penalty_applies_to_either_veto(self) -> None:
        stuck = BarrierScore(
            at=(0, 0), escape_reduction=48, chain=4, disconnects=False, immobilises=True
        )
        assert stuck.total < 0
        assert not stuck.permitted

    def test_a_refused_candidate_is_still_scored_and_logged(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Silently dropping it leaves a transcript with an unexplained gap."""
        state = board((0, 0), (2, 2), grid_size=3, barriers={(1, 0)})
        with caplog.at_level(logging.INFO, logger="cop_agent.strategy.barriers"):
            best_placement(state, AXES, (2, 2))
        assert "(0, 1)" in caplog.text
        assert "CUTS-SELF-OFF" in caplog.text

    def test_having_no_permitted_placement_is_logged(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        state = board((0, 0), (2, 2), grid_size=3, barriers={(0, 1), (1, 0)})
        with caplog.at_level(logging.INFO, logger="cop_agent.strategy.barriers"):
            best_placement(state, AXES, (2, 2))
        assert "every candidate is refused" in caplog.text

    def test_the_open_board_is_unaffected(self) -> None:
        """The constraint must not quietly narrow ordinary play."""
        state = board((3, 3), (5, 5))
        assert len(safe_placements(state, AXES, (5, 5))) == 5
