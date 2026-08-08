from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_mcp_client")).items() if not k.startswith("__")})

class TestOnlyTransportFailuresAreRetried:
    @pytest.mark.parametrize(
        "failure",
        [TimeoutError("no answer"), ConnectionError("refused"), OSError("network down")],
    )
    def test_a_transport_fault_is_transient_and_retried(self, failure: Exception) -> None:
        transport = FakeTransport(failure, {"ok": True})
        assert OpponentClient(transport, SETTINGS).call("receive_turn", {}) == {"ok": True}
    @pytest.mark.parametrize(
        "failure",
        [ValueError("malformed"), KeyError("missing"), RuntimeError("bug")],
    )
    def test_anything_else_is_a_bug_and_is_not_retried(self, failure: Exception) -> None:
        transport = FakeTransport(failure)
        with pytest.raises(type(failure)):
            OpponentClient(transport, SETTINGS).call("receive_turn", {})
        assert len(transport.calls) == 1
