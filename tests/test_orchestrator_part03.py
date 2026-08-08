from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_orchestrator")).items() if not k.startswith("__")})

class TestTimeoutBecomesARecordedCause:
    def test_exhausted_retries_abort_with_timeout(self) -> None:
        orch, _ = orchestrator(*[TimeoutError()] * 10)
        with pytest.raises(MatchAborted) as excinfo:
            orch.call_opponent("receive_turn", {})
        assert excinfo.value.cause is TechnicalLoss.TIMEOUT
    def test_the_cause_carries_detail_for_agreeing_a_result(self) -> None:
        orch, _ = orchestrator(*[TimeoutError()] * 10)
        with pytest.raises(MatchAborted) as excinfo:
            orch.call_opponent("receive_turn", {})
        assert "after 4 attempts" in excinfo.value.detail
    def test_a_recoverable_failure_does_not_abort(self) -> None:
        orch, _ = orchestrator(TimeoutError(), {"ok": True})
        assert orch.call_opponent("receive_turn", {})["ok"] is True
