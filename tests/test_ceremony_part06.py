from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_ceremony")).items() if not k.startswith("__")})

class TestAcknowledging:
    def test_acknowledging_nothing_is_refused(self) -> None:
        ceremony = StepCeremony(step=4, role="police")
        ceremony.commit(commitment(), OUR_NONCE)
        with pytest.raises(CeremonyError, match="has not committed"):
            ceremony.acknowledge(WHEN)
    def test_an_acknowledgement_before_we_commit_is_refused(self) -> None:
        ceremony = StepCeremony(step=4, role="police")
        with pytest.raises(CeremonyError, match="before we committed"):
            ceremony.receive_ack(
                Acknowledgement(step=4, sender="thief", acknowledges=DIGEST, timestamp=WHEN)
            )
    def test_an_acknowledgement_of_some_other_digest_is_refused(self) -> None:
        ceremony = opened()
        with pytest.raises(CeremonyError, match="never made"):
            ceremony.receive_ack(
                Acknowledgement(step=4, sender="thief", acknowledges="c" * 64, timestamp=WHEN)
            )
    def test_an_acknowledgement_from_the_wrong_role_is_refused(self) -> None:
        ceremony = opened()
        with pytest.raises(CeremonyError, match="expected 'thief'"):
            ceremony.receive_ack(
                Acknowledgement(step=4, sender="police", acknowledges=DIGEST, timestamp=WHEN)
            )
