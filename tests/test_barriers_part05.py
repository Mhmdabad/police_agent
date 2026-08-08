from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_barriers")).items() if not k.startswith("__")})

class TestDecisionIsLogged:
    def test_every_candidate_and_its_breakdown_reaches_the_log(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.INFO, logger="cop_agent.strategy.barriers"):
            rank_placements(board((3, 3), (5, 5)), AXES, (5, 5))
        assert "escape-" in caplog.text and "chain+" in caplog.text
        assert caplog.text.count("total=") == 5
    def test_an_empty_candidate_set_is_logged_too(self, caplog: pytest.LogCaptureFixture) -> None:
        state = board((0, 0), (2, 2), grid_size=3, barriers={(0, 0), (0, 1), (1, 0)})
        with caplog.at_level(logging.INFO, logger="cop_agent.strategy.barriers"):
            rank_placements(state, AXES, (2, 2))
        assert "every cell in reach is sealed" in caplog.text
    def test_a_self_cutting_candidate_says_so(self, caplog: pytest.LogCaptureFixture) -> None:
        state = board((0, 0), (2, 2), grid_size=3, barriers={(1, 0)})
        with caplog.at_level(logging.INFO, logger="cop_agent.strategy.barriers"):
            rank_placements(state, AXES, (2, 2))
        assert "CUTS-SELF-OFF" in caplog.text
