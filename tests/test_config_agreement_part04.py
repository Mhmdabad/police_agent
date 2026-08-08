from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_config_agreement")).items() if not k.startswith("__")})

class TestSilenceFailsClosed:
    def test_a_peer_that_never_negotiates_produces_a_timeout(self, wire: tuple[Side, Side]) -> None:
        ours, _ = fresh(wire)
        with pytest.raises(MatchAborted) as excinfo:
            ours.orchestrator.agree_config(parameters(), game_uid=GAME_UID, timeout=BRIEF)
        assert excinfo.value.cause is TechnicalLoss.TIMEOUT
    def test_it_fails_inside_its_own_window_rather_than_hanging(
        self, wire: tuple[Side, Side]
    ) -> None:
        ours, _ = fresh(wire)
        started = time.monotonic()
        with pytest.raises(MatchAborted):
            ours.orchestrator.agree_config(parameters(), game_uid=GAME_UID, timeout=BRIEF)
        assert time.monotonic() - started < 15.0, "the gate hung instead of failing closed"
    def test_the_opponent_acknowledged_us_all_the_same(self, wire: tuple[Side, Side]) -> None:
        ours, theirs = fresh(wire)
        with pytest.raises(MatchAborted):
            ours.orchestrator.agree_config(parameters(), game_uid=GAME_UID, timeout=BRIEF)
        assert theirs.inboxes.digests.qsize() == 1
