from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_stage5_tunnel_drop")).items() if not k.startswith("__")})

class TestTheWatchdogSeesRetryingRatherThanStalling:
    def test_a_retrying_client_keeps_the_watchdog_satisfied(self) -> None:
        now = [0.0]
        dog = Watchdog(clock=lambda: now[0])
        tunnel = Tunnel()
        orch = peer(tunnel)
        orch.on_event = lambda _: dog.beat()
        tunnel.kill()
        with pytest.raises(MatchAborted):
            orch.call_opponent("receive_turn", TURN)
        now[0] = 50.0  # well into the 135s a real drop would take
        assert dog.check() is WatchdogVerdict.ALIVE
        assert dog.beats >= 4  # one per attempt, at least
    def test_without_the_beats_the_watchdog_would_fire(self) -> None:
        now = [0.0]
        dog = Watchdog(clock=lambda: now[0])
        now[0] = DEFAULT_WATCHDOG_TIMEOUT_SEC + 1
        assert dog.check() is WatchdogVerdict.SHUTDOWN
