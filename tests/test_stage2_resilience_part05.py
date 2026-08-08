from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_stage2_resilience")).items() if not k.startswith("__")})

class TestHostileInputDoesNotCrash:
    def test_a_malformed_payload_is_refused_not_raised(self) -> None:
        orch = orchestrator(DeadTransport(alive_calls=1))
        assert orch.handle_inbound("receive_turn", None)["ok"] is False
    def test_an_unknown_tool_is_refused(self) -> None:
        orch = orchestrator(DeadTransport(alive_calls=1))
        assert orch.handle_inbound("drop_tables", {})["ok"] is False
    def test_a_refusal_is_recorded_for_the_dispute(self) -> None:
        orch = orchestrator(DeadTransport(alive_calls=1))
        orch.handle_inbound("receive_turn", None)
        assert orch.inboxes.rejected
