from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_localhost_match")).items() if not k.startswith("__")})

class TestEachSideAuditsTheOther:
    def test_the_cop_finds_the_thief_honest(self, played: tuple[Side, Side, Path]) -> None:
        cop, _, _ = played
        result = played_game(cop).audit()
        assert result.clean, str(result)
        assert result.checked == STEPS
    def test_the_thief_finds_the_cop_honest(self, played: tuple[Side, Side, Path]) -> None:
        _, thief, _ = played
        result = played_game(thief).audit()
        assert result.clean, str(result)
        assert result.checked == STEPS
    def test_both_kept_the_board_each_step_was_sealed_against(
        self, played: tuple[Side, Side, Path]
    ) -> None:
        cop, thief, _ = played
        for step in range(1, STEPS + 1):
            assert played_game(cop).sealed_states[step] == played_game(thief).sealed_states[step]
    def test_each_received_the_others_nonces(self, played: tuple[Side, Side, Path]) -> None:
        cop, thief, _ = played
        assert played_game(cop).their_final is not None
        assert played_game(thief).their_final is not None
        theirs = played_game(cop).their_final
        assert theirs is not None
        assert sorted(theirs.nonces) == [1, 2, 3]
