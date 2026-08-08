from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_ceremony")).items() if not k.startswith("__")})

class TestTheNonceStaysHidden:
    def test_the_wire_form_has_no_nonce(self) -> None:
        assert tuple(reveal().to_dict()) == REVEAL_FIELDS
        assert "nonce" not in json.dumps(reveal().to_dict())
    def test_an_inbound_nonce_is_refused_rather_than_ignored(self) -> None:
        with pytest.raises(CeremonyError, match="carries a nonce"):
            Reveal.from_dict({**reveal().to_dict(), "nonce": "0" * 32})
    def test_it_round_trips_through_json(self) -> None:
        opened = reveal(barrier_placed=[2, 2])
        assert Reveal.from_dict(json.loads(json.dumps(opened.to_dict()))) == opened
    @pytest.mark.parametrize("intent", ["maybe", "TRUTH", ""])
    def test_an_intent_outside_the_two_is_refused(self, intent: str) -> None:
        with pytest.raises(CeremonyError, match="intent must be one of"):
            reveal(intent=intent)
    @pytest.mark.parametrize("sender", ["cop", "referee", ""])
    def test_a_role_the_wire_does_not_name_is_refused(self, sender: str) -> None:
        with pytest.raises(CeremonyError, match="sender must be one of"):
            reveal(sender=sender)
    def test_a_negative_step_is_refused(self) -> None:
        with pytest.raises(CeremonyError, match="step must be >= 0"):
            reveal(step=-1)
    @pytest.mark.parametrize(
        "payload", ["not a mapping", {}, {"step": 4, "sender": "police", "move": "N"}]
    )
    def test_a_malformed_reveal_is_one_error_type(self, payload: object) -> None:
        with pytest.raises(CeremonyError):
            Reveal.from_dict(payload)
