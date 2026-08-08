from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_barriers")).items() if not k.startswith("__")})

class TestSelfPenalty:
    def test_walling_ourselves_off_is_flagged(self) -> None:
        state = board((0, 0), (2, 2), grid_size=3, barriers={(1, 0)})
        assert score_placement(state, (0, 1), AXES, (2, 2)).disconnects
    def test_the_penalty_outweighs_any_real_gain(self) -> None:
        cut = BarrierScore(at=(0, 1), escape_reduction=48, chain=4, disconnects=True)
        assert cut.total < 0
        assert SELF_PENALTY > 49 + 4
    def test_a_placement_that_keeps_the_route_is_not_flagged(self) -> None:
        assert not score_placement(board((3, 3), (5, 5)), (3, 4), AXES, (5, 5)).disconnects
    def test_sealing_our_own_cell_is_not_cutting_ourselves_off(self) -> None:
        state = board((3, 3), (5, 5))
        sealed = replace(state, barriers=frozenset({(3, 3)}))
        assert legal_moves(sealed, "cop", AXES) == ["N", "S", "E", "W"]
        assert reachable(sealed, (3, 3), AXES) == frozenset()
        assert not score_placement(state, (3, 3), AXES, (5, 5)).disconnects
    def test_sealing_our_own_cell_in_a_dead_end_does_cut_us_off(self) -> None:
        state = board((0, 0), (2, 2), grid_size=3, barriers={(1, 0), (0, 1)})
        assert score_placement(state, (0, 0), AXES, (2, 2)).disconnects
