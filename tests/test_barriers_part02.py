from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_barriers")).items() if not k.startswith("__")})

class TestEscapeReduction:
    def test_open_board_placement_reduces_by_one(self) -> None:
        state = board((3, 3), (5, 5))
        assert score_placement(state, (3, 3), AXES, (5, 5)).escape_reduction == 1
    def test_closing_a_corridor_takes_the_whole_region(self) -> None:
        state = board((1, 1), (0, 0), grid_size=3, barriers={(0, 1)})
        score = score_placement(state, (1, 0), AXES, (0, 0))
        assert score.escape_reduction == 7
        assert reachable_area(state, (0, 0), AXES) == 8
    def test_a_barrier_the_thief_cannot_reach_costs_it_nothing(self) -> None:
        state = board((2, 2), (0, 0), grid_size=3, barriers={(0, 1), (1, 0)})
        assert score_placement(state, (2, 2), AXES, (0, 0)).escape_reduction == 0
