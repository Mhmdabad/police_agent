from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_ceremony")).items() if not k.startswith("__")})

class TestParsingWhatArrives:
    def test_it_round_trips(self) -> None:
        assert Commitment.from_dict(commitment().to_dict()) == commitment()
    def test_it_survives_json(self) -> None:
        assert Commitment.from_dict(json.loads(json.dumps(commitment().to_dict()))) == commitment()
    def test_unbound_legacy_commitment_fails_closed(self) -> None:
        legacy = commitment().to_dict()
        legacy.pop("game_uid")
        legacy.pop("sub_game")
        with pytest.raises(CeremonyError, match="game_uid"):
            Commitment.from_dict(legacy)
    def test_extra_fields_are_dropped_rather_than_refused(self) -> None:
        smuggled = {**commitment().to_dict(), "move": "N", "hint": "uptown"}
        parsed = Commitment.from_dict(smuggled)
        assert parsed == commitment()
        assert not hasattr(parsed, "move")
    @pytest.mark.parametrize(
        "payload",
        [
            "not a mapping",
            {},
            {"step": 4, "sender": "police", "commit": DIGEST},
            {"step": "four", "sender": "police", "commit": DIGEST, "timestamp": WHEN},
            {"step": 4, "sender": "police", "commit": 42, "timestamp": WHEN},
        ],
    )
    def test_a_malformed_commitment_is_one_error_type(self, payload: object) -> None:
        with pytest.raises(CeremonyError):
            Commitment.from_dict(payload)
