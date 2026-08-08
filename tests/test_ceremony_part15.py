from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_ceremony")).items() if not k.startswith("__")})

class TestAnHonestMatchAuditsClean:
    def test_every_step_is_re_derived_and_matches(self) -> None:
        match, disclosed, states = honest_match()
        result = audit_opponent(match, disclosed, states)
        assert result.clean
        assert result.checked == 3
        assert "3 steps re-derived, all matching" in str(result)
    def test_a_step_they_never_committed_to_is_not_audited(self) -> None:
        match, disclosed, states = honest_match()
        match.at(9).commit(commitment(step=9), OUR_NONCE)
        result = audit_opponent(match, disclosed, states)
        assert result.clean
        assert result.checked == 3
    def test_a_match_with_nothing_committed_is_vacuously_clean(self) -> None:
        result = audit_opponent(MatchCeremony(role="police"), FinalReveal("thief", {}, WHEN), {})
        assert result.clean
        assert result.checked == 0
