from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_scent_runtime")).items() if not k.startswith("__")})

class TestTheAgentActuallyEmits:
    def test_a_played_sub_game_lays_a_trail(self) -> None:
        game, _ = a_subgame()
        game.play()
        assert game.scent.outgoing()
    def test_standing_still_emits_too(self) -> None:
        game, _ = a_subgame(moves=["STAY", "STAY", "STAY"])
        game.play()
        for step in (1, 2, 3):
            opened = game.ceremony.at(step).revealed_ours
            assert opened is not None and opened.scent is not None
            assert opened.scent[f"{OUR_START[0]},{OUR_START[1]}"] == CENTRE_INTENSITY
    def test_a_barrier_turn_would_emit_from_where_the_cop_stands(self) -> None:
        game, _ = a_subgame(moves=["STAY"], max_steps=1)
        game.play()
        assert game.scent.own.strongest() == OUR_START
    def test_the_emission_follows_the_move_that_was_committed(self) -> None:
        game, _ = a_subgame(moves=[AWAY, AWAY], max_steps=2)
        game.play()
        opened = game.ceremony.at(2).revealed_ours
        assert opened is not None and opened.scent is not None
        assert opened.scent[f"{TWO_AWAY[0]},{TWO_AWAY[1]}"] == CENTRE_INTENSITY
