from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_mcp_client")).items() if not k.startswith("__")})

class TestRetryBudget:
    def test_recovers_from_a_transient_failure(self) -> None:
        transport = FakeTransport(TimeoutError(), {"ok": True})
        client = OpponentClient(transport, SETTINGS)
        assert client.call("ping", {}) == {"ok": True}
        assert client.attempts == 2
    def test_gives_up_once_the_budget_is_spent(self) -> None:
        transport = FakeTransport(*[TimeoutError()] * 10)
        client = OpponentClient(transport, SETTINGS)
        with pytest.raises(OpponentUnreachableError, match="after 4 attempts"):
            client.call("ping", {})
        assert client.attempts == 4
    def test_backs_off_between_attempts(self) -> None:
        slept: list[float] = []
        transport = FakeTransport(TimeoutError(), TimeoutError(), {"ok": True})
        settings = dataclasses.replace(SETTINGS, retry_backoff_sec=5.0)
        OpponentClient(transport, settings, sleep=slept.append).call("ping", {})
        assert slept == [5.0, 5.0]
    def test_default_backoff_uses_wall_clock_sleep(self, monkeypatch: pytest.MonkeyPatch) -> None:
        slept: list[float] = []
        monkeypatch.setattr("cop_agent.infra.mcp_client.time.sleep", slept.append)
        transport = FakeTransport(TimeoutError(), {"ok": True})
        settings = dataclasses.replace(SETTINGS, retry_backoff_sec=5.0)
        OpponentClient(transport, settings).call("ping", {})
        assert slept == [5.0]
    def test_does_not_sleep_after_the_final_attempt(self) -> None:
        slept: list[float] = []
        transport = FakeTransport(*[TimeoutError()] * 10)
        settings = dataclasses.replace(SETTINGS, retry_backoff_sec=5.0, max_retries=1)
        with pytest.raises(OpponentUnreachableError):
            OpponentClient(transport, settings, sleep=slept.append).call("ping", {})
        assert slept == [5.0]
