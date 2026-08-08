from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_token_bucket")).items() if not k.startswith("__")})

class TestBackoffGrowsAndThenStops:
    def test_the_first_backoff_is_the_configured_base(self) -> None:
        assert Limiter().backoff_for(1) == 5.0
    def test_it_doubles(self) -> None:
        limiter = Limiter()
        assert [limiter.backoff_for(n) for n in (1, 2, 3)] == [5.0, 10.0, 20.0]
    def test_asking_past_max_retries_raises_rather_than_returning_a_sentinel(self) -> None:
        with pytest.raises(RateLimitError, match="retries exhausted"):
            Limiter().backoff_for(MAX_RETRIES + 1)
    def test_attempts_are_numbered_from_one(self) -> None:
        with pytest.raises(RateLimitError, match="numbered from 1"):
            Limiter().backoff_for(0)
