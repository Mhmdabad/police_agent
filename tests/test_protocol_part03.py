from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_protocol")).items() if not k.startswith("__")})

class TestAuditPayload:
    def test_round_trips(self) -> None:
        payload = {
            "sender": "thief",
            "records": [{"payload": {"step": 0}, "nonce": "n", "commit": "c"}],
            "result_claim": "survival",
            "game_uid": "series-123",
            "sub_game": 2,
        }
        assert AuditPayload.from_dict(payload).to_dict() == payload
    def test_records_must_be_a_list(self) -> None:
        with pytest.raises(InvalidPayloadError, match="records"):
            AuditPayload.from_dict({"sender": "thief", "records": {}, "result_claim": "x"})
    def test_each_record_must_be_an_object(self) -> None:
        with pytest.raises(InvalidPayloadError):
            AuditPayload.from_dict({"sender": "thief", "records": ["x"], "result_claim": "y"})
    def test_result_claim_is_required(self) -> None:
        with pytest.raises(InvalidPayloadError):
            AuditPayload.from_dict({"sender": "thief", "records": []})
    def test_series_and_sub_game_binding_are_required(self) -> None:
        base = {"sender": "thief", "records": [], "result_claim": "survival"}
        with pytest.raises(InvalidPayloadError, match="game_uid"):
            AuditPayload.from_dict(base)
        with pytest.raises(InvalidPayloadError, match="sub_game"):
            AuditPayload.from_dict({**base, "game_uid": "series-123"})
