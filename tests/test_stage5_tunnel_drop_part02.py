from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_stage5_tunnel_drop")).items() if not k.startswith("__")})

class TestItStaysInsideTheDeadlineBudget:
    def test_the_backoff_is_bounded_by_the_retry_count(self) -> None:
        slept: list[float] = []
        tunnel = Tunnel()
        orch = peer(tunnel, slept=slept)
        tunnel.kill()
        with pytest.raises(MatchAborted):
            orch.call_opponent("receive_turn", TURN)
        assert slept == [5.0, 5.0, 5.0]  # three gaps between four attempts
    def test_no_attempt_waits_longer_than_the_response_timeout(self) -> None:
        windows: list[float] = []
        tunnel = Tunnel(elapsed=windows)
        orch = peer(tunnel)
        tunnel.kill()
        with pytest.raises(MatchAborted):
            orch.call_opponent("receive_turn", TURN)
        assert windows == [DEFAULT_RESPONSE_TIMEOUT_SEC] * 4
    def test_the_worst_case_is_stated_rather_than_discovered(self) -> None:
        settings = ClientSettings(opponent_url=LIVE_URL)
        assert settings.worst_case_seconds == 4 * 30.0 + 3 * 5.0
    def test_the_worst_case_outlives_the_watchdog_and_that_is_the_point(self) -> None:
        settings = ClientSettings(opponent_url=LIVE_URL)
        assert settings.worst_case_seconds > DEFAULT_WATCHDOG_TIMEOUT_SEC
    def test_raising_max_retries_moves_the_worst_case(self) -> None:
        settings = ClientSettings(opponent_url=LIVE_URL, max_retries=6)
        assert settings.worst_case_seconds == 7 * 30.0 + 6 * 5.0
