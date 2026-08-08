from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_strategy")).items() if not k.startswith("__")})

class TestManhattan:
    def test_matches_the_rulebook_worked_example(self) -> None:
        assert manhattan((2, 2), (5, 5)) == 6
    def test_is_symmetric(self) -> None:
        assert manhattan((1, 2), (4, 6)) == manhattan((4, 6), (1, 2))
    def test_a_cell_is_zero_from_itself(self) -> None:
        assert manhattan((3, 3), (3, 3)) == 0
    def test_ignores_barriers(self) -> None:
        assert manhattan((0, 0), (0, 2)) == 2
