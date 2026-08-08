from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_stage2_resilience")).items() if not k.startswith("__")})

class TestWatchdogFreeze:
    def test_a_frozen_loop_shuts_down_controlled(self) -> None:
        clock = FakeClock()
        events: list[str] = []
        dog = Watchdog(
            timeout_sec=60.0,
            clock=clock,
            persist_state=lambda: events.append("persist"),
            shutdown=lambda: events.append("shutdown"),
        )
        clock.advance(61.0)
        assert dog.check() is WatchdogVerdict.SHUTDOWN
        assert events == ["persist", "shutdown"]
    def test_state_is_persisted_before_the_process_stops(self) -> None:
        clock = FakeClock()
        events: list[str] = []
        dog = Watchdog(
            timeout_sec=10.0,
            clock=clock,
            persist_state=lambda: events.append("persist"),
            shutdown=lambda: events.append("shutdown"),
        )
        clock.advance(999.0)
        dog.check()
        assert events.index("persist") < events.index("shutdown")
    def test_a_busy_loop_is_never_mistaken_for_a_frozen_one(self) -> None:
        clock = FakeClock()
        dog = Watchdog(timeout_sec=60.0, clock=clock)
        for _ in range(50):
            clock.advance(59.0)
            dog.beat()
        assert dog.check() is WatchdogVerdict.ALIVE
