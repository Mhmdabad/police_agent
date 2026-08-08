from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_ceremony")).items() if not k.startswith("__")})

class TestOnlyTheHashCrossesTheWire:
    def test_the_wire_form_is_exactly_the_declared_fields(self) -> None:
        assert tuple(commitment().to_dict()) == COMMIT_FIELDS
    def test_it_carries_nothing_that_narrows_the_search_space(self) -> None:
        wire = json.dumps(commitment().to_dict())
        for leak in ("move", "hint", "intent", "barrier", "nonce", "cop", "thief", "state"):
            assert leak not in wire
    def test_a_real_commitment_reveals_nothing_about_its_record(self) -> None:
        record = step_record(BOARD, "police", "N", "lie", "heading uptown", barrier_placed=(2, 2))
        wire = json.dumps(commitment(commit=commit_of(record, "0" * 32)).to_dict())
        assert "heading uptown" not in wire
        assert "N" not in wire.replace("2026", "")  # the timestamp is allowed its digits
    def test_two_different_records_are_indistinguishable_on_the_wire(self) -> None:
        north = commit_of(step_record(BOARD, "police", "N", "truth", "north"), "0" * 32)
        south = commit_of(step_record(BOARD, "police", "S", "lie", "somewhere else"), "0" * 32)
        assert len(north) == len(south)
        assert set(commitment(commit=north).to_dict()) == set(commitment(commit=south).to_dict())
