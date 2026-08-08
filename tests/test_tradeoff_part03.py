from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_tradeoff")).items() if not k.startswith("__")})

class TestBothSidesAreLogged:
    def test_the_figures_that_justified_it_are_in_the_transcript(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        state = board(cop=(2, 1), thief=(2, 5), barriers=CORRIDOR)
        with caplog.at_level(logging.INFO, logger="cop_agent.strategy.tradeoff"):
            weigh(state, AXES, (2, 5), "E")
        assert "PLACE" in caplog.text
        assert "removes 14" in caplog.text
        assert "vs move closing 1" in caplog.text
        assert "budget:" in caplog.text
    def test_a_refusal_is_logged_just_as_loudly(self, caplog: pytest.LogCaptureFixture) -> None:
        with caplog.at_level(logging.INFO, logger="cop_agent.strategy.tradeoff"):
            weigh(board(cop=(0, 0), thief=(3, 3)), AXES, (3, 3), "S")
        assert "MOVE" in caplog.text
    def test_the_endgame_is_marked(self, caplog: pytest.LogCaptureFixture) -> None:
        pocket = {(0, 4), (1, 4)} | {(2, col) for col in range(4)}
        state = board(cop=(0, 3), thief=(0, 0), barriers=pocket)
        with caplog.at_level(logging.INFO, logger="cop_agent.strategy.tradeoff"):
            weigh(state, AXES, (0, 0), "W")
        assert "endgame" in caplog.text
