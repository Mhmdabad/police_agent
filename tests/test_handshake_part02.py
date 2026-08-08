from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_handshake")).items() if not k.startswith("__")})

class TestParsingWhatArrives:
    def test_it_round_trips(self) -> None:
        original = greet("thief", PUBLIC_THIEF)
        assert Greeting.from_dict(original.to_dict()) == original
    def test_it_survives_json(self) -> None:
        original = greet("thief", PUBLIC_THIEF)
        assert Greeting.from_dict(json.loads(json.dumps(original.to_dict()))) == original
    @pytest.mark.parametrize(
        "payload",
        [
            "not a mapping",
            {},
            {"role": "police"},
            {"role": "police", "group_id": "g", "public_url": PUBLIC_COP},
            {"role": "police", "group_id": "g", "public_url": 42, "protocol_version": "1.0"},
            {"role": "police", "group_id": "g", "public_url": "ftp://x", "protocol_version": "1.0"},
        ],
    )
    def test_it_refuses_a_malformed_greeting_as_one_error_type(self, payload: object) -> None:
        with pytest.raises(HandshakeError):
            Greeting.from_dict(payload)
