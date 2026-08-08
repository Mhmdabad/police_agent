from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_scent_runtime")).items() if not k.startswith("__")})

class TestDecayHappensOncePerFullTurn:
    def test_an_abandoned_cell_keeps_ninety_percent_a_turn(self) -> None:
        game, _ = a_subgame(moves=["STAY", AWAY, AWAY], max_steps=3)
        game.play()
        assert game.scent.own.intensity_at(OUR_START) == pytest.approx(
            CENTRE_INTENSITY * RETENTION**3, abs=1e-9
        )
    def test_exactly_one_decay_follows_a_single_turn(self) -> None:
        game, _ = a_subgame(moves=["STAY"], max_steps=1)
        game.play()
        assert game.scent.own.intensity_at(OUR_START) == pytest.approx(
            CENTRE_INTENSITY * RETENTION, abs=1e-9
        )
