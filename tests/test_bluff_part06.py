from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_bluff")).items() if not k.startswith("__")})

class TestLandmarks:
    def test_it_names_the_closest_one(self) -> None:
        assert nearest_landmark((0, 3), BOARD) == "uptown"
    def test_landmarks_scale_with_the_board(self) -> None:
        big = BoardState(cop=(0, 0), thief=(3, 3), grid_size=11)
        assert nearest_landmark((10, 10), big) == nearest_landmark((6, 6), BOARD)
    def test_every_named_place_is_one_the_parser_knows(self) -> None:
        for hint in every_hint():
            named = [word for word in hint.lower().split() if word in LANDMARKS]
            assert named, hint
