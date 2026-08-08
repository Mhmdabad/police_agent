from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_bluff")).items() if not k.startswith("__")})

class TestItDescribesARegion:
    def test_a_hint_names_a_direction_or_a_landmark(self) -> None:
        for hint in every_hint():
            spoken = set(hint.lower().replace(",", " ").split())
            assert spoken & (set(DIRECTIONS) | set(LANDMARKS)), hint
    def test_only_compass_words_the_parser_reads_back(self) -> None:
        assert all(word in DIRECTIONS for word, _ in COMPASS)
    def test_the_larger_displacement_wins(self) -> None:
        assert bearing((3, 3), (0, 4)) == "north"
        assert bearing((3, 3), (4, 6)) == "east"
    def test_a_zero_displacement_still_yields_a_word(self) -> None:
        assert bearing((3, 3), (3, 3)) in DIRECTIONS
