from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_stage2_resilience")).items() if not k.startswith("__")})

class TestIllegalTransition:
    def test_it_raises_rather_than_stalling(self) -> None:
        machine = GamePhaseMachine()
        with pytest.raises(IllegalTransitionError):
            machine.to(Phase.AWAITING_REVEAL)
    def test_the_phase_is_unchanged_after_a_refusal(self) -> None:
        machine = GamePhaseMachine()
        with pytest.raises(IllegalTransitionError):
            machine.to(Phase.AWAITING_REVEAL)
        assert machine.phase is Phase.WAITING_FOR_OPPONENT
    def test_acting_out_of_turn_raises_too(self) -> None:
        with pytest.raises(OutOfTurnError):
            TurnScheduler().record("thief")
    def test_the_machine_can_still_abort_cleanly_afterwards(self) -> None:
        machine = GamePhaseMachine()
        with pytest.raises(IllegalTransitionError):
            machine.to(Phase.VERIFYING)
        assert machine.abort("gave up") is Phase.TECHNICAL_LOSS
