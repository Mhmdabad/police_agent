from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_scent_audit")).items() if not k.startswith("__")})

class TestTheFieldIsBoundToThePhaseOneCommitment:
    def record(self, field: dict[str, float] | None) -> dict[str, Any]:
        return step_record(START, OUR_ROLE, OUR_STEP[1], "truth", "uptown", scent=field)
    def test_the_sealed_record_carries_the_field(self) -> None:
        field = snapshot_at(OUR_START)
        assert self.record(field)["scent"] == field
    def test_a_turn_without_scent_seals_null_rather_than_omitting_the_key(self) -> None:
        assert self.record(None)["scent"] is None
    def test_changing_one_cell_after_the_commit_breaks_it(self) -> None:
        honest_field = snapshot_at(OUR_START)
        tampered = {**honest_field, f"{OUR_START[0]},{OUR_START[1]}": 0.899}
        assert commit_of(self.record(honest_field), "0" * 32) != commit_of(
            self.record(tampered), "0" * 32
        )
    def test_the_binding_survives_a_json_round_trip(self) -> None:
        import json
        field = snapshot_at((3, 3))
        assert commit_of(self.record(field), "0" * 32) == commit_of(
            self.record(json.loads(json.dumps(field))), "0" * 32
        )
