from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_scent_runtime")).items() if not k.startswith("__")})

class TestOnlyTheOpponentsFieldIsAbsorbed:
    def test_their_trail_arrives(self) -> None:
        game, _ = a_subgame()
        game.play()
        assert game.scent.opponent.strongest() == THEIR_START
    def test_our_own_field_is_never_mixed_in(self) -> None:
        game, _ = a_subgame(moves=["STAY", "STAY", "STAY"])
        game.play()
        assert game.scent.own.intensity_at(OUR_START) > 0.5
        assert game.scent.opponent.intensity_at(OUR_START) == 0.0
    def test_a_field_we_cannot_verify_is_not_absorbed(self) -> None:
        game, _ = a_subgame(ScentedOpponent(junk=True), moves=["STAY"])
        game.play()
        assert game.scent.opponent.values == {}
    def test_an_omitted_field_absorbs_nothing(self) -> None:
        game, _ = a_subgame(ScentedOpponent(omit=True))
        game.play()
        assert game.scent.opponent.values == {}
