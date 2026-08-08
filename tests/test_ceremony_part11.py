from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_ceremony")).items() if not k.startswith("__")})

class TestTheFinalRevealMessage:
    def test_it_carries_every_nonce_keyed_by_step(self) -> None:
        match = played()
        match.finish()
        assert match.final_reveal(WHEN).nonces == {1: OUR_NONCE, 2: OUR_NONCE, 3: OUR_NONCE}
    def test_step_keys_become_strings_on_the_wire(self) -> None:
        match = played(steps=1)
        match.finish()
        assert match.final_reveal(WHEN).to_dict()["nonces"] == {"1": OUR_NONCE}
    def test_it_round_trips_through_json(self) -> None:
        match = played()
        match.finish()
        disclosed = match.final_reveal(WHEN)
        assert FinalReveal.from_dict(json.loads(json.dumps(disclosed.to_dict()))) == disclosed
    @pytest.mark.parametrize("bad", ["0" * 31, "0" * 33, "Z" * 32, ""])
    def test_a_nonce_that_is_not_one_is_refused(self, bad: str) -> None:
        with pytest.raises(CeremonyError, match="hex characters"):
            FinalReveal(sender="police", nonces={1: bad}, timestamp=WHEN)
    @pytest.mark.parametrize("sender", ["cop", "referee", ""])
    def test_a_role_the_wire_does_not_name_is_refused(self, sender: str) -> None:
        with pytest.raises(CeremonyError, match="sender must be one of"):
            FinalReveal(sender=sender, nonces={1: OUR_NONCE}, timestamp=WHEN)
    def test_a_negative_step_is_refused(self) -> None:
        with pytest.raises(CeremonyError, match="step must be >= 0"):
            FinalReveal(sender="police", nonces={-1: OUR_NONCE}, timestamp=WHEN)
    def test_a_step_key_that_is_not_an_integer_is_refused(self) -> None:
        with pytest.raises(CeremonyError, match="not an integer"):
            FinalReveal.from_dict(
                {"sender": "police", "nonces": {"one": OUR_NONCE}, "timestamp": WHEN}
            )
    @pytest.mark.parametrize(
        "payload",
        [
            "not a mapping",
            {"sender": "police", "timestamp": WHEN},
            {"sender": "police", "nonces": [], "timestamp": WHEN},
            {"sender": "police", "nonces": {"1": 42}, "timestamp": WHEN},
        ],
    )
    def test_a_malformed_final_reveal_is_one_error_type(self, payload: object) -> None:
        with pytest.raises(CeremonyError):
            FinalReveal.from_dict(payload)
