from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_protocol")).items() if not k.startswith("__")})

class TestControlMessage:
    def test_round_trips(self) -> None:
        parsed = ControlMessage.from_dict({"kind": "status", "sender": "police"})
        assert parsed.kind == "status"
        assert parsed.sub_game_number == 1
    def test_an_unknown_kind_is_refused(self) -> None:
        with pytest.raises(InvalidPayloadError, match="must be one of"):
            ControlMessage.from_dict({"kind": "selfdestruct", "sender": "police"})
    def test_it_is_not_part_of_the_sealed_record(self) -> None:
        assert (
            "commit" not in ControlMessage.from_dict({"kind": "quit", "sender": "thief"}).to_dict()
        )
