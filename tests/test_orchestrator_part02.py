from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_orchestrator")).items() if not k.startswith("__")})

class TestHeartbeat:
    def test_inbound_and_outbound_both_beat(self) -> None:
        orch, _ = orchestrator()
        orch.handle_inbound("receive_turn", TURN)
        orch.call_opponent("receive_turn", {})
        assert orch.heartbeats == [
            "inbound:receive_turn",
            "outbound:receive_turn",
            "attempt:receive_turn",
        ]
    def test_every_retry_attempt_beats(self) -> None:
        orch, _ = orchestrator(TimeoutError(), TimeoutError(), {"ok": True})
        orch.call_opponent("receive_turn", {})
        assert orch.heartbeats.count("attempt:receive_turn") == 3
    def test_events_are_published(self) -> None:
        orch, _ = orchestrator()
        seen: list[str] = []
        orch.on_event = seen.append
        orch.handle_inbound("negotiate", {})
        assert seen == ["inbound:negotiate"]
