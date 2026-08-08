from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_ceremony")).items() if not k.startswith("__")})

class TestTheLockGate:
    def test_nothing_is_locked_before_anything_happens(self) -> None:
        assert not StepCeremony(step=4, role="police").locked
    def test_two_commitments_alone_are_not_a_lock(self) -> None:
        assert not opened().locked
    def test_our_acknowledgement_alone_is_not_a_lock(self) -> None:
        ceremony = opened()
        ceremony.acknowledge(WHEN)
        assert not ceremony.locked
    def test_theirs_alone_is_not_a_lock(self) -> None:
        ceremony = opened()
        ceremony.receive_ack(
            Acknowledgement(step=4, sender="thief", acknowledges=DIGEST, timestamp=WHEN)
        )
        assert not ceremony.locked
    def test_all_four_parts_are_a_lock(self) -> None:
        assert both_locked().locked
    def test_the_opponent_is_whichever_role_is_not_ours(self) -> None:
        assert StepCeremony(step=4, role="police").opponent == "thief"
        assert StepCeremony(step=4, role="thief").opponent == "police"
    def test_a_ceremony_needs_a_real_role(self) -> None:
        with pytest.raises(CeremonyError, match="role must be one of"):
            StepCeremony(step=4, role="cop")
