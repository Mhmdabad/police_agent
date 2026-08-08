from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_token_bucket")).items() if not k.startswith("__")})

class TestTheFormula:
    def test_it_starts_full_because_silence_earns_burst(self) -> None:
        assert bucket().tokens() == 2.0
    def test_allow_spends_a_token(self) -> None:
        gate = bucket()
        assert gate.allow()
        assert gate.tokens() == 1.0
    def test_it_blocks_when_empty(self) -> None:
        gate = bucket()
        assert gate.allow()
        assert gate.allow()
        assert not gate.allow()
    def test_it_refills_at_r_times_delta_t(self) -> None:
        clock = Clock()
        gate = bucket(clock)
        gate.allow()
        gate.allow()
        clock.advance(2.0)  # r = 30/60 = 0.5 tokens/sec
        assert gate.tokens() == pytest.approx(1.0)
    def test_refill_is_capped_at_c(self) -> None:
        clock = Clock()
        gate = bucket(clock)
        gate.allow()
        gate.allow()
        clock.advance(10_000.0)
        assert gate.tokens() == 2.0
    def test_silence_really_is_rewarded(self) -> None:
        clock = Clock()
        gate = bucket(clock)
        gate.allow()
        gate.allow()
        assert not gate.allow()
        clock.advance(60.0)
        assert gate.allow() and gate.allow(), "a quiet minute should buy back the burst"
    def test_the_rate_is_per_minute_divided_by_sixty(self) -> None:
        assert bucket(per_minute=30.0).rate == pytest.approx(0.5)
