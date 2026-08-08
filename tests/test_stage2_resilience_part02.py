from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_stage2_resilience")).items() if not k.startswith("__")})

class TestOpponentKilledMidTurn:
    def test_the_retry_budget_is_spent_then_the_match_aborts(self) -> None:
        transport = DeadTransport()
        with pytest.raises(MatchAborted) as excinfo:
            orchestrator(transport).call_opponent("ping", {})
        assert excinfo.value.cause is TechnicalLoss.TIMEOUT
        assert transport.calls == 4
    def test_the_abort_carries_a_cause_that_can_be_agreed(self) -> None:
        with pytest.raises(MatchAborted) as excinfo:
            orchestrator(DeadTransport()).call_opponent("ping", {})
        assert "after 4 attempts" in excinfo.value.detail
    def test_dying_partway_through_still_terminates(self) -> None:
        transport = DeadTransport(alive_calls=1)
        orch = orchestrator(transport)
        assert orch.call_opponent("ping", {})["ok"]
        with pytest.raises(MatchAborted):
            orch.call_opponent("ping", {})
    def test_the_phase_machine_can_record_the_loss(self) -> None:
        machine = GamePhaseMachine()
        machine.to(Phase.COMPUTING_MOVE)
        machine.to(Phase.COMMITTING)
        machine.to(Phase.AWAITING_REVEAL)
        assert machine.abort("opponent gone") is Phase.TECHNICAL_LOSS
        assert machine.is_terminal
