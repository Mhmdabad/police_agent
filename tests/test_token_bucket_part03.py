from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_token_bucket")).items() if not k.startswith("__")})

class TestWaitForReportsRatherThanSleeps:
    def test_it_is_zero_when_a_token_is_available(self) -> None:
        assert bucket().wait_for() == 0.0
    def test_it_is_the_time_to_earn_one_token(self) -> None:
        gate = bucket()
        gate.allow()
        gate.allow()
        assert gate.wait_for() == pytest.approx(2.0), "0.5 tokens/sec, so one token is 2s"
    def test_it_shrinks_as_time_passes(self) -> None:
        clock = Clock()
        gate = bucket(clock)
        gate.allow()
        gate.allow()
        clock.advance(1.0)
        assert gate.wait_for() == pytest.approx(1.0)
    def test_it_does_not_spend_a_token(self) -> None:
        gate = bucket()
        gate.wait_for()
        assert gate.tokens() == 2.0
