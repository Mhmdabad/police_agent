from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_ceremony")).items() if not k.startswith("__")})

class TestTheAcknowledgementMessage:
    def test_it_names_the_digest_rather_than_saying_yes(self) -> None:
        ack = opened().acknowledge(WHEN)
        assert ack.acknowledges == THEIR_DIGEST
        assert tuple(ack.to_dict()) == ACK_FIELDS
    def test_it_round_trips_through_json(self) -> None:
        ack = opened().acknowledge(WHEN)
        assert Acknowledgement.from_dict(json.loads(json.dumps(ack.to_dict()))) == ack
    @pytest.mark.parametrize("digest", ["a" * 63, "A" * 64, "", "zz"])
    def test_it_refuses_a_digest_that_is_not_one(self, digest: str) -> None:
        with pytest.raises(CeremonyError, match="64 lowercase hex"):
            Acknowledgement(step=4, sender="police", acknowledges=digest, timestamp=WHEN)
    @pytest.mark.parametrize("sender", ["cop", "referee", ""])
    def test_it_refuses_a_role_the_wire_does_not_name(self, sender: str) -> None:
        with pytest.raises(CeremonyError, match="sender must be one of"):
            Acknowledgement(step=4, sender=sender, acknowledges=DIGEST, timestamp=WHEN)
    def test_it_refuses_a_negative_step(self) -> None:
        with pytest.raises(CeremonyError, match="step must be >= 0"):
            Acknowledgement(step=-1, sender="police", acknowledges=DIGEST, timestamp=WHEN)
    @pytest.mark.parametrize(
        "payload",
        ["not a mapping", {}, {"step": 4, "sender": "police", "acknowledges": DIGEST}],
    )
    def test_a_malformed_acknowledgement_is_one_error_type(self, payload: object) -> None:
        with pytest.raises(CeremonyError):
            Acknowledgement.from_dict(payload)
