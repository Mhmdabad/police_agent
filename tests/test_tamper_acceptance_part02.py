from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_tamper_acceptance")).items() if not k.startswith("__")})

class TestEveryFieldOfTheRecordIsCovered:
    @pytest.mark.parametrize("field", ["state", "role", "move", "intent", "hint", "barrier_placed"])
    @pytest.mark.parametrize("index", range(STEPS))
    def test_altering_one_field_of_one_step_is_caught(
        self, tmp_path: Path, field: str, index: int
    ) -> None:
        def edit(body: dict[str, Any]) -> None:
            row = body["steps"][index]["reveal"]
            row[field] = swapped(row[field])
        result = walk(load(by_hand(honest_log(tmp_path), edit)))
        assert result.stamp is Stamp.TAMPERED
        assert result.at_step == index + 1
    @pytest.mark.parametrize("field", ["grid_size", "step", "self", "barriers"])
    def test_altering_one_field_inside_the_board_is_caught(
        self, tmp_path: Path, field: str
    ) -> None:
        def edit(body: dict[str, Any]) -> None:
            board = body["steps"][0]["reveal"]["state"]
            board[field] = swapped(board[field])
        assert stamp_after(tmp_path, edit) is Stamp.TAMPERED
    def test_adding_a_field_the_committer_never_wrote_is_caught(self, tmp_path: Path) -> None:
        def edit(body: dict[str, Any]) -> None:
            body["steps"][0]["reveal"]["note"] = "added later"
        assert stamp_after(tmp_path, edit) is Stamp.TAMPERED
    def test_removing_a_field_is_caught(self, tmp_path: Path) -> None:
        def edit(body: dict[str, Any]) -> None:
            del body["steps"][0]["reveal"]["hint"]
        assert stamp_after(tmp_path, edit) is Stamp.TAMPERED
