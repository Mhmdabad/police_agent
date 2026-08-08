from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_ceremony")).items() if not k.startswith("__")})

class TestCommittingOnce:
    def test_a_second_commitment_of_ours_is_refused(self) -> None:
        ceremony = StepCeremony(step=4, role="police")
        ceremony.commit(commitment(), OUR_NONCE)
        with pytest.raises(CeremonyError, match="not revisable"):
            ceremony.commit(commitment(commit="c" * 64), OUR_NONCE)
    def test_a_second_commitment_of_theirs_is_refused(self) -> None:
        ceremony = opened()
        with pytest.raises(CeremonyError, match="already locked"):
            ceremony.receive(their_commitment(commit="c" * 64))
    def test_a_commitment_for_another_step_is_refused(self) -> None:
        ceremony = StepCeremony(step=4, role="police")
        with pytest.raises(CeremonyError, match="is for step 9"):
            ceremony.commit(commitment(step=9), OUR_NONCE)
    def test_our_own_role_is_expected_on_our_commitment(self) -> None:
        ceremony = StepCeremony(step=4, role="police")
        with pytest.raises(CeremonyError, match="expected 'police'"):
            ceremony.commit(their_commitment(), OUR_NONCE)
    def test_the_opponents_role_is_expected_on_theirs(self) -> None:
        ceremony = StepCeremony(step=4, role="police")
        with pytest.raises(CeremonyError, match="expected 'thief'"):
            ceremony.receive(commitment())
