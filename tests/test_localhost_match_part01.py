from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_localhost_match")).items() if not k.startswith("__")})

class TestTheMatchActuallyHappened:
    def test_both_sides_played_every_step(self, played: tuple[Side, Side, Path]) -> None:
        cop, thief, _ = played
        assert sorted(cop.runner.outcomes[0].log.entries) == [1, 2, 3]
        assert sorted(thief.runner.outcomes[0].log.entries) == [1, 2, 3]
    def test_nothing_was_rejected(self, played: tuple[Side, Side, Path]) -> None:
        cop, thief, _ = played
        assert cop.inboxes.rejected == []
        assert thief.inboxes.rejected == []
    def test_neither_side_had_to_knock_twice(self, played: tuple[Side, Side, Path]) -> None:
        cop, thief, _ = played
        assert cop.inboxes.deferred == []
        assert thief.inboxes.deferred == []
    def test_each_side_holds_the_others_commitments(self, played: tuple[Side, Side, Path]) -> None:
        cop, thief, _ = played
        for step in (1, 2, 3):
            assert played_game(cop).ceremony.at(step).theirs is not None
            assert played_game(thief).ceremony.at(step).theirs is not None
    def test_the_digests_match_across_the_wire(self, played: tuple[Side, Side, Path]) -> None:
        cop, thief, _ = played
        for step in (1, 2, 3):
            ours = played_game(cop).ceremony.at(step).ours
            theirs = played_game(thief).ceremony.at(step).theirs
            assert ours is not None and theirs is not None
            assert ours.commit == theirs.commit
