from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_subgame")).items() if not k.startswith("__")})

class TestTheCeremonyIsReal:
    def test_the_opponents_audit_of_us_is_clean(self, tmp_path: Path) -> None:
        game, peer, _ = a_subgame(tmp_path, max_steps=3)
        game.play()
        assert peer.ceremony.steps, "the stand-in never received anything"
    def test_a_corrupted_reveal_is_not_caught_at_reveal_time(self, tmp_path: Path) -> None:
        game, _, _ = a_subgame(tmp_path, StandInOpponent(corrupt_at=2), max_steps=3)
        game.play()  # the sub-game completes; the lie is still on the record
    def test_the_material_to_catch_it_is_all_recorded(self, tmp_path: Path) -> None:
        game, _, _ = a_subgame(tmp_path, StandInOpponent(corrupt_at=2), max_steps=3)
        game.play()
        for step in (1, 2, 3):
            ceremony = game.ceremony.at(step)
            assert ceremony.theirs is not None
            assert ceremony.revealed_theirs is not None
    def test_an_unreadable_revealed_move_is_named(self, tmp_path: Path) -> None:
        game, _, _ = a_subgame(tmp_path, max_steps=1)
        game._peer_reveals[1] = Reveal(  # noqa: SLF001
            step=1,
            sender="thief",
            move="sideways",
            intent="truth",
            hint="somewhere",
            timestamp=WHEN,
        )
        with pytest.raises(UnplayableReveal, match="not a move"):
            game.peer_move(1)
