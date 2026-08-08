from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_scent_runtime")).items() if not k.startswith("__")})

class TestTheFieldTravelsInPhaseThreeOnly:
    def test_the_commitment_we_send_carries_no_field(self) -> None:
        game, opponent = a_subgame(max_steps=2)
        game.play()
        for commitment in opponent.commits:
            assert "scent" not in commitment.to_dict()
            assert "smell_grid" not in commitment.to_dict()
    def test_our_reveal_carries_the_field_we_sealed(self) -> None:
        game, _ = a_subgame(max_steps=2)
        game.play()
        for step in (1, 2):
            opened = game.ceremony.at(step).revealed_ours
            assert opened is not None
            assert opened.scent
    def test_the_log_records_the_field_the_commitment_covers(self) -> None:
        game, _ = a_subgame(max_steps=2)
        game.play()
        entry = game.log.entries[1]
        assert entry.reveal is not None
        assert entry.reveal["scent"]
