from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_token_bucket")).items() if not k.startswith("__")})

class TestTheQueueIsWhereBackpressureLives:
    def test_a_request_with_a_token_available_waits_for_nothing(self) -> None:
        assert Limiter(bucket=bucket()).enter() == 0.0
    def test_a_request_with_no_token_is_told_how_long_to_wait(self) -> None:
        limiter = Limiter(bucket=bucket())
        limiter.enter()
        limiter.enter()
        assert limiter.enter() == pytest.approx(2.0)
    def test_only_waiting_requests_occupy_the_queue(self) -> None:
        limiter = Limiter(bucket=bucket())
        limiter.enter()
        assert limiter.waiting == 0, "a request that went straight through is not waiting"
    def test_a_full_queue_refuses_rather_than_growing(self) -> None:
        limiter = Limiter(bucket=bucket(), queue_depth=QUEUE_DEPTH)
        limiter.enter()
        limiter.enter()
        for _ in range(QUEUE_DEPTH):
            limiter.enter()
        with pytest.raises(QueueFull, match="queue depth is 100"):
            limiter.enter()
    def test_queue_full_is_a_rate_limit_error(self) -> None:
        assert issubclass(QueueFull, RateLimitError)
    def test_leaving_frees_a_slot(self) -> None:
        limiter = Limiter(bucket=bucket())
        limiter.enter()
        limiter.enter()
        limiter.enter()
        assert limiter.waiting == 1
        limiter.leave()
        assert limiter.waiting == 0
    def test_leaving_more_often_than_entering_does_not_go_negative(self) -> None:
        limiter = Limiter(bucket=bucket())
        limiter.leave()
        limiter.leave()
        assert limiter.waiting == 0
