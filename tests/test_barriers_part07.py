from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_barriers")).items() if not k.startswith("__")})

class TestOnePlacementWin:
    def test_a_barrier_on_the_thiefs_cell_is_a_trapping_capture(self) -> None:
        state = board((3, 3), (3, 4))
        assert winning_placement(state, AXES) == (3, 4)
        assert wins_outright(state, (3, 4), AXES)
    def test_it_needs_the_thief_within_placement_reach(self) -> None:
        state = board((3, 3), (3, 5))
        assert winning_placement(state, AXES) is None
    def test_closing_the_last_side_is_an_enclosure_capture(self) -> None:
        state = board((0, 2), (0, 0), barriers={(1, 0)})
        assert winning_placement(state, AXES) == (0, 1)
    def test_two_open_sides_is_not_one_placement_away(self) -> None:
        state = board((0, 2), (0, 0))
        assert winning_placement(state, AXES) is None
    def test_no_win_returns_none_rather_than_a_guess(self) -> None:
        assert winning_placement(board((0, 0), (5, 5)), AXES) is None
    def test_an_exhausted_quota_is_not_a_win(self) -> None:
        state = board((3, 3), (3, 4))
        assert winning_placement(state, AXES, max_barriers=0) is None
    def test_the_last_barrier_still_buys_it(self) -> None:
        walls = {(6, col) for col in range(7)}
        state = board((3, 3), (3, 4), barriers=walls)
        assert state.barriers_used == 7
        assert winning_placement(state, AXES, max_barriers=8) == (3, 4)
    def test_the_winning_cell_is_ranked_last_by_value(self) -> None:
        state = board((3, 3), (3, 4))
        ranked = rank_placements(state, AXES, (3, 4))
        assert ranked[-1].at == winning_placement(state, AXES)
    def test_the_self_preservation_gate_would_veto_the_win(self) -> None:
        state = board((3, 3), (3, 4))
        win = winning_placement(state, AXES)
        assert win is not None
        vetoed = next(score for score in rank_placements(state, AXES, (3, 4)) if score.at == win)
        assert vetoed.disconnects
        assert not vetoed.permitted
        assert win not in {score.at for score in safe_placements(state, AXES, (3, 4))}
    def test_the_same_holds_for_the_enclosure_win(self) -> None:
        state = board((0, 2), (0, 0), barriers={(1, 0)})
        win = winning_placement(state, AXES)
        chosen = best_placement(state, AXES, (0, 0))
        assert win == (0, 1)
        assert chosen is not None and chosen.at != win
    def test_candidates_are_ordered_before_anything_reads_them(self) -> None:
        state = board((3, 3), (5, 5))
        assert candidates(state, AXES) == sorted(candidates(state, AXES))
    def test_an_already_sealed_cell_is_not_a_candidate(self) -> None:
        state = board((3, 3), (5, 5), barriers={(2, 3)})
        assert (2, 3) not in candidates(state, AXES)
    def test_an_already_won_position_yields_no_placement(self) -> None:
        trapped = board((3, 3), (3, 4), barriers={(3, 4)})
        assert winning_placement(trapped, AXES) is None
        overlapped = board((3, 3), (3, 3))
        assert winning_placement(overlapped, AXES) is None
