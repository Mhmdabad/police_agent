from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_token_bucket")).items() if not k.startswith("__")})

class TestRefillIsComputedNotTicked:
    def test_a_process_that_was_stopped_for_an_hour_comes_back_full(self) -> None:
        clock = Clock()
        gate = bucket(clock)
        gate.allow()
        gate.allow()
        clock.advance(3600.0)
        assert gate.tokens() == 2.0
    def test_a_clock_that_steps_backwards_does_not_break_it(self) -> None:
        clock = Clock()
        gate = bucket(clock)
        gate.allow()
        before = gate.tokens()
        clock.advance(-500.0)
        assert gate.tokens() == pytest.approx(before), "Δt is clamped at zero, not negative"
    def test_asking_repeatedly_does_not_add_tokens(self) -> None:
        gate = bucket(Clock())
        gate.allow()
        for _ in range(50):
            gate.tokens()
        assert gate.tokens() == 1.0
