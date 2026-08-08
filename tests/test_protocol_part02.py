from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_protocol")).items() if not k.startswith("__")})

class TestTurnMessage:
    def test_round_trips(self) -> None:
        assert TurnMessage.from_dict(TURN).to_dict()["commit"] == TURN["commit"]
    def test_optional_fields_default_to_none(self) -> None:
        parsed = TurnMessage.from_dict(TURN)
        assert parsed.barrier_placed is None
        assert parsed.capture_claim is None
        assert parsed.win_claim is None
    def test_carries_a_whole_turn_in_one_message(self) -> None:
        rich = {**TURN, "barrier_placed": [2, 3], "capture_claim": [4, 4]}
        parsed = TurnMessage.from_dict(rich)
        assert parsed.barrier_placed == [2, 3]
        assert parsed.capture_claim == [4, 4]
    def test_the_true_position_is_not_on_the_wire(self) -> None:
        assert "position" not in TurnMessage.from_dict(TURN).to_dict()
    @pytest.mark.parametrize("missing", ["step", "sender", "commit", "timestamp"])
    def test_required_fields_are_enforced(self, missing: str) -> None:
        body = {k: v for k, v in TURN.items() if k != missing}
        with pytest.raises(InvalidPayloadError):
            TurnMessage.from_dict(body)
    def test_an_unknown_sender_is_refused(self) -> None:
        with pytest.raises(InvalidPayloadError, match="must be one of"):
            TurnMessage.from_dict({**TURN, "sender": "referee"})
    def test_cop_is_not_a_wire_role(self) -> None:
        with pytest.raises(InvalidPayloadError):
            TurnMessage.from_dict({**TURN, "sender": "cop"})
    def test_a_malformed_cell_is_refused(self) -> None:
        with pytest.raises(InvalidPayloadError, match="pair"):
            TurnMessage.from_dict({**TURN, "barrier_placed": [1, 2, 3]})
    def test_a_boolean_coordinate_is_refused(self) -> None:
        with pytest.raises(InvalidPayloadError, match="integers"):
            TurnMessage.from_dict({**TURN, "capture_claim": [True, 3]})
    def test_a_non_object_smell_grid_is_refused(self) -> None:
        with pytest.raises(InvalidPayloadError, match="smell_grid"):
            TurnMessage.from_dict({**TURN, "smell_grid": []})
    def test_smell_grid_keys_stay_strings(self) -> None:
        parsed = TurnMessage.from_dict(TURN)
        assert all(isinstance(k, str) for k in parsed.smell_grid)
