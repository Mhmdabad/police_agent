from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_orchestrator")).items() if not k.startswith("__")})

class TestMatchAbortedSurvivesPropagation:
    @contextlib.contextmanager
    def turn(self) -> Iterator[None]:
        yield
    def test_it_keeps_its_cause_through_a_context_manager(self) -> None:
        with pytest.raises(MatchAborted) as excinfo, self.turn():
            raise MatchAborted(TechnicalLoss.TIMEOUT, "tunnel died at step 12")
        assert excinfo.value.cause is TechnicalLoss.TIMEOUT
        assert excinfo.value.detail == "tunnel died at step 12"
    def test_it_can_carry_a_traceback(self) -> None:
        try:
            raise MatchAborted(TechnicalLoss.CRASH, "peer exited")
        except MatchAborted as exc:
            assert exc.__traceback__ is not None
    def test_it_survives_nested_context_managers(self) -> None:
        with pytest.raises(MatchAborted), self.turn(), self.turn():
            raise MatchAborted(TechnicalLoss.FORGERY, "commit did not match reveal")
    def test_frozen_was_the_actual_culprit_not_slots(self) -> None:
        aborted = MatchAborted(TechnicalLoss.TIMEOUT, "detail")
        aborted.__traceback__ = None
        assert (aborted.cause, aborted.detail) == (TechnicalLoss.TIMEOUT, "detail")
