from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_crypto")).items() if not k.startswith("__")})

class TestTheFullStepRecord:
    def record(self, **overrides: object) -> dict[str, object]:
        fields: dict[str, Any] = {
            "state": BOARD,
            "role": "police",
            "move": "N",
            "intent": "lie",
            "hint": "heading uptown",
        }
        return step_record(**{**fields, **overrides})
    def test_it_carries_the_four_named_fields_and_the_four_implied_ones(self) -> None:
        assert set(self.record()) == {
            "state",
            "role",
            "move",
            "intent",
            "hint",
            "barrier_placed",
            "scent",
            "game_uid",
            "sub_game",
        }
        assert self.record()["state"]["step"] == 4  # type: ignore[index]
    def test_a_barrier_placement_is_sealed(self) -> None:
        assert self.record(barrier_placed=(2, 2))["barrier_placed"] == [2, 2]
    def test_a_turn_without_a_barrier_seals_null_rather_than_omitting_the_key(self) -> None:
        assert self.record()["barrier_placed"] is None
        assert self.record(role="thief")["barrier_placed"] is None
    def test_changing_any_field_changes_the_commitment(self) -> None:
        base = commit_of(self.record(), "n")
        for changed in (
            self.record(move="S"),
            self.record(intent="truth"),
            self.record(hint="downtown"),
            self.record(barrier_placed=(2, 2)),
        ):
            assert commit_of(changed, "n") != base
    def test_it_round_trips_through_json_unchanged(self) -> None:
        sealed = self.record(barrier_placed=(2, 2))
        assert commit_of(json.loads(canonical(sealed)), "n") == commit_of(sealed, "n")
    def test_a_sealed_record_verifies(self) -> None:
        sealed = self.record(barrier_placed=(2, 2))
        opened = seal(sealed)
        verify(sealed, opened["nonce"], opened["commit"])
