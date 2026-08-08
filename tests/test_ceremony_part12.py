from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_ceremony")).items() if not k.startswith("__")})

class TestNoncesAreDisclosedOnlyAtTheEnd:
    def test_disclosing_mid_match_is_refused(self) -> None:
        with pytest.raises(CeremonyError, match="while the match is running"):
            played().final_reveal(WHEN)
    def test_the_nonce_never_leaves_by_any_other_path(self) -> None:
        ceremony = both_locked()
        assert ceremony.our_nonce == OUR_NONCE
        assert OUR_NONCE not in json.dumps(commitment().to_dict())
        assert OUR_NONCE not in json.dumps(reveal().to_dict())
    def test_a_malformed_nonce_is_refused_at_commit_time(self) -> None:
        ceremony = StepCeremony(step=4, role="police")
        with pytest.raises(CeremonyError, match="hex characters"):
            ceremony.commit(commitment(), "not-a-nonce")
