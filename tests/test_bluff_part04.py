from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_bluff")).items() if not k.startswith("__")})

class TestDeterminism:
    def test_the_same_seed_gives_the_same_sentence(self) -> None:
        assert compose((5, 1), BOARD, (3, 3), random.Random(4)) == compose(
            (5, 1), BOARD, (3, 3), random.Random(4)
        )
    def test_the_nearest_landmark_is_stable_under_ties(self) -> None:
        assert nearest_landmark((3, 3), BOARD) == nearest_landmark((3, 3), BOARD)
    def test_it_works_without_an_rng(self) -> None:
        assert compose((5, 1), BOARD, (3, 3))
