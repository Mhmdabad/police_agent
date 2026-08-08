from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_subgame")).items() if not k.startswith("__")})

class TestTheEdgesOfTheLoop:
    def test_a_step_the_opponent_has_not_revealed_yields_nothing(self, tmp_path: Path) -> None:
        game, _, _ = a_subgame(tmp_path, max_steps=1)
        assert game.peer_move(1) is None
    def test_the_board_still_advances_when_they_did_not_move(self, tmp_path: Path) -> None:
        game, _, _ = a_subgame(tmp_path, max_steps=1)
        before = game.state
        game.state = game.state
        game._advance(MoveAction(move="E"), None)  # noqa: SLF001
        assert game.state.cop != before.cop
    def test_reasoning_reaches_the_log_when_the_brain_supplies_it(self, tmp_path: Path) -> None:
        game, _, log = a_subgame(tmp_path, max_steps=1)
        original = game.brain.decide
        def with_reasoning(state: BoardState, **context: object) -> Decision:
            decision = original(state, **context)
            decision.reasoning = "closing the north gap"
            return decision
        game.brain.decide = with_reasoning  # type: ignore[method-assign]
        game.play()
        assert log.entries[1].discussion == {
            "intent": "truth",
            "reasoning": "closing the north gap",
        }
