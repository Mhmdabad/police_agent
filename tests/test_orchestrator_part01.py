from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_orchestrator")).items() if not k.startswith("__")})

class TestSingleGateway:
    def test_inbound_reaches_the_mailboxes(self) -> None:
        orch, _ = orchestrator()
        assert orch.handle_inbound("receive_turn", TURN)["ok"] is True
        assert orch.inboxes.turns.get_nowait().step == 1
    def test_inbound_is_delegated_not_revalidated(self) -> None:
        orch, _ = orchestrator()
        assert orch.handle_inbound("receive_turn", None)["ok"] is False
        assert orch.inboxes.rejected
    def test_an_unknown_tool_is_refused(self) -> None:
        orch, _ = orchestrator()
        assert orch.handle_inbound("drop_tables", {})["ok"] is False
    def test_every_wire_tool_is_routed(self) -> None:
        orch, _ = orchestrator()
        for tool in ("negotiate", "receive_turn", "submit_audit", "receive_control"):
            assert "ok" in orch.handle_inbound(tool, {})
    def test_no_game_rule_lives_here(self) -> None:
        import cop_agent.runtime.orchestrator as module
        source = Path(module.__file__ or "").read_text()
        for rule_word in ("legal_moves", "apply_move", "is_capture", "BOOK_SCORES"):
            assert rule_word not in source
