from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_tradeoff")).items() if not k.startswith("__")})

class TestDistanceClosed:
    def test_a_step_toward_the_target_closes_one(self) -> None:
        assert distance_closed(board(cop=(0, 0)), "S", (3, 3), AXES) == 1
    def test_standing_still_closes_nothing(self) -> None:
        assert distance_closed(board(cop=(0, 0)), "STAY", (3, 3), AXES) == 0
    def test_a_step_away_is_reported_as_a_loss(self) -> None:
        assert distance_closed(board(cop=(1, 1)), "N", (3, 3), AXES) == -1
