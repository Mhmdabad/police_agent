from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_ceremony")).items() if not k.startswith("__")})

class TestTheMatchCeremony:
    def test_it_opens_a_step_on_first_reference_and_reuses_it(self) -> None:
        match = MatchCeremony(role="police")
        assert match.at(3) is match.at(3)
        assert match.at(3).role == "police"
    def test_it_needs_a_real_role(self) -> None:
        with pytest.raises(CeremonyError, match="role must be one of"):
            MatchCeremony(role="cop")
    def test_the_opponent_is_whichever_role_is_not_ours(self) -> None:
        assert MatchCeremony(role="police").opponent == "thief"
        assert MatchCeremony(role="thief").opponent == "police"
