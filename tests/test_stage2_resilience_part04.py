from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_stage2_resilience")).items() if not k.startswith("__")})

class TestDeadlinesAndWatchdogAreDifferentGuards:
    def test_a_deadline_fires_while_the_loop_is_healthy(self) -> None:
        clock = FakeClock()
        tracker = DeadlineTracker(timeout_sec=30.0, clock=clock)
        dog = Watchdog(timeout_sec=60.0, clock=clock)
        deadline = tracker.start("commit")
        clock.advance(31.0)
        dog.beat()
        with pytest.raises(DeadlineExpiredError):
            tracker.check(deadline)
        assert dog.check() is WatchdogVerdict.ALIVE
    def test_the_watchdog_fires_with_no_request_outstanding(self) -> None:
        clock = FakeClock()
        tracker = DeadlineTracker(timeout_sec=30.0, clock=clock)
        dog = Watchdog(timeout_sec=60.0, clock=clock)
        clock.advance(61.0)
        assert tracker.expired_count() == 0
        assert dog.check() is WatchdogVerdict.SHUTDOWN
