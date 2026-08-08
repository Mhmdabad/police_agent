from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_bluff")).items() if not k.startswith("__")})

class TestIntentIsChosenFirst:
    def test_intent_is_an_argument_not_a_result(self) -> None:
        assert speak((5, 1), BOARD, (3, 3), "truth").intent == "truth"
        assert speak((5, 1), BOARD, (3, 3), "lie").intent == "lie"
    def test_a_truthful_hint_points_at_where_we_are(self) -> None:
        assert speak((5, 1), BOARD, (3, 3), "truth").about == (5, 1)
    def test_a_lie_points_elsewhere(self) -> None:
        assert speak((5, 1), BOARD, (3, 3), "lie").about != (5, 1)
    @pytest.mark.parametrize("bad", ["maybe", "TRUTH", "", "bluff"])
    def test_an_unknown_intent_is_refused(self, bad: str) -> None:
        with pytest.raises(ValueError, match="intent must be one of"):
            speak((5, 1), BOARD, (3, 3), bad)
    def test_the_flag_travels_with_the_text(self) -> None:
        spoken = speak((5, 1), BOARD, (3, 3), "lie")
        assert spoken.text and spoken.intent == "lie" and spoken.about
