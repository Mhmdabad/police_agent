from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_token_bucket")).items() if not k.startswith("__")})

class TestTheAppendixFMinimumsAreFloorsNotDefaults:
    def test_the_constants_come_from_the_table_not_from_here(self) -> None:
        assert book_value("rate_limiter_gatekeeper", "requests_per_minute") == REQUESTS_PER_MINUTE
        assert book_value("rate_limiter_gatekeeper", "concurrent_requests") == CONCURRENT_REQUESTS
        assert book_value("rate_limiter_gatekeeper", "queue_depth") == QUEUE_DEPTH
        assert book_value("rate_limiter_gatekeeper", "max_retries") == MAX_RETRIES
        assert book_value("rate_limiter_gatekeeper", "retry_backoff_sec") == RETRY_BACKOFF_SEC
    def test_the_book_values_are_what_the_rulebook_prints(self) -> None:
        assert (REQUESTS_PER_MINUTE, CONCURRENT_REQUESTS) == (30, 2)
        assert (RETRY_BACKOFF_SEC, MAX_RETRIES, QUEUE_DEPTH) == (5, 3, 100)
    def test_a_rate_below_the_minimum_is_refused(self) -> None:
        with pytest.raises(RateLimitError, match="minimum in Appendix F"):
            TokenBucket(per_minute=29.0)
    def test_a_capacity_below_the_minimum_is_refused(self) -> None:
        with pytest.raises(RateLimitError, match="concurrent_requests is a minimum"):
            TokenBucket(capacity=1.0)
    def test_going_above_a_minimum_is_allowed(self) -> None:
        assert TokenBucket(per_minute=120.0, capacity=10.0).tokens() == 10.0
    @pytest.mark.parametrize(
        "lowered",
        [{"queue_depth": 99}, {"max_retries": 2}, {"backoff_sec": 4.0}],
    )
    def test_the_limiter_refuses_each_minimum_being_lowered(self, lowered: dict[str, Any]) -> None:
        with pytest.raises(RateLimitError, match="minimum in Appendix F"):
            Limiter(**lowered)
    def test_the_defaults_are_the_book_values(self) -> None:
        limiter = Limiter()
        assert limiter.queue_depth == QUEUE_DEPTH
        assert limiter.max_retries == MAX_RETRIES
        assert limiter.backoff_sec == float(RETRY_BACKOFF_SEC)
