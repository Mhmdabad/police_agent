from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_subgame")).items() if not k.startswith("__")})

class TestTheBranchesARoleReversalReaches:
    @staticmethod
    def as_thief(tmp_path: Path) -> SubGame:
        log = MatchLog(game_id="uoh26-s82kma9e", sub_game=1, role="thief", game_uid="u-1")
        return SubGame(
            role="thief",
            brain=PoliceBrain(),
            peer=StandInOpponent(),
            log=log,
            state=board(),
            axes=AXES,
            max_steps=1,
            now=lambda: WHEN,
        )
    def test_a_barrier_from_the_cop_is_playable(self, tmp_path: Path) -> None:
        game = self.as_thief(tmp_path)
        game._peer_reveals[1] = Reveal(  # noqa: SLF001
            step=1,
            sender="police",
            move="barrier",
            intent="truth",
            hint="somewhere",
            timestamp=WHEN,
            barrier_placed=[2, 3],
        )
        action = game.peer_move(1)
        assert isinstance(action, PlaceBarrier)
        assert action.at == (2, 3)
    def test_a_barrier_from_the_thief_is_refused(self, tmp_path: Path) -> None:
        game, _, _ = a_subgame(tmp_path, max_steps=1)
        game._peer_reveals[1] = Reveal(  # noqa: SLF001
            step=1,
            sender="thief",
            move="barrier",
            intent="truth",
            hint="somewhere",
            timestamp=WHEN,
            barrier_placed=[2, 3],
        )
        with pytest.raises(UnplayableReveal, match="only the cop may place"):
            game.peer_move(1)
