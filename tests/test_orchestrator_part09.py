from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_orchestrator")).items() if not k.startswith("__")})

class TestForgeryBecomesAResult:
    def orchestrated(self) -> Orchestrator:
        orch, _ = orchestrator()
        return orch
    def test_a_clean_match_returns_the_result(self) -> None:
        from test_ceremony import honest_match
        match, disclosed, states = honest_match()
        result = self.orchestrated().audit(match, disclosed, states)
        assert result.clean and result.checked == 3
    def test_a_forged_step_aborts_with_forgery(self) -> None:
        from test_ceremony import honest_match, reveal
        match, disclosed, states = honest_match()
        match.steps[2].revealed_theirs = reveal(
            step=2, sender="thief", move="W", intent="truth", hint="hint 2"
        )
        with pytest.raises(MatchAborted) as excinfo:
            self.orchestrated().audit(match, disclosed, states)
        assert excinfo.value.cause is TechnicalLoss.FORGERY
    def test_the_arithmetic_travels_with_the_accusation(self) -> None:
        from test_ceremony import honest_match, reveal
        match, disclosed, states = honest_match()
        match.steps[1].revealed_theirs = reveal(
            step=1, sender="thief", move="W", intent="truth", hint="hint 1"
        )
        with pytest.raises(MatchAborted) as excinfo:
            self.orchestrated().audit(match, disclosed, states)
        assert "step 1" in excinfo.value.detail and "produces" in excinfo.value.detail
    def test_the_audit_beats_so_the_watchdog_sees_it(self) -> None:
        from test_ceremony import honest_match
        match, disclosed, states = honest_match()
        orch = self.orchestrated()
        orch.audit(match, disclosed, states)
        assert "audit" in orch.heartbeats
