from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_replay")).items() if not k.startswith("__")})

class TestItRefusesWhatItCannotVouchFor:
    def test_a_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(ReplayError, match="cannot read"):
            load(tmp_path / "absent.json")
    def test_a_file_that_is_not_json(self, tmp_path: Path) -> None:
        path = tmp_path / "log_g_g01.json"
        path.write_text("{ not json")
        with pytest.raises(ReplayError, match="is not JSON"):
            load(path)
    def test_a_json_document_that_is_not_a_log(self, tmp_path: Path) -> None:
        path = tmp_path / "log_g_g01.json"
        path.write_text("[1, 2, 3]")
        with pytest.raises(ReplayError, match="not a match log object"):
            load(path)
    def test_a_log_with_no_steps_list(self, tmp_path: Path) -> None:
        path = tmp_path / "log_g_g01.json"
        path.write_text('{"game_id": "g"}')
        with pytest.raises(ReplayError, match="no 'steps' list"):
            load(path)
    def test_an_empty_sub_game(self, tmp_path: Path) -> None:
        path = tmp_path / "log_g_g01.json"
        path.write_text('{"game_id": "g", "steps": []}')
        with pytest.raises(ReplayError, match="no steps cannot be replayed"):
            load(path)
    def test_a_step_missing_a_slot(self, tmp_path: Path) -> None:
        path = edited(tmp_path, lambda body: body["steps"][2].pop("commit"))
        with pytest.raises(ReplayError, match=r"missing \['commit'\]"):
            load(path)
    def test_a_deleted_step_leaves_a_gap_that_is_allowed_but_visible(self, tmp_path: Path) -> None:
        path = edited(tmp_path, lambda body: body["steps"].pop(1))
        assert load(path).numbers() == [1, 3, 4]
    def test_steps_out_of_order(self, tmp_path: Path) -> None:
        path = edited(tmp_path, lambda body: body["steps"].reverse())
        with pytest.raises(ReplayError, match="out of order"):
            load(path)
    def test_a_repeated_step_number(self, tmp_path: Path) -> None:
        path = edited(tmp_path, lambda body: body["steps"].append(dict(body["steps"][0])))
        with pytest.raises(ReplayError, match="repeats a step number"):
            load(path)
    def test_a_non_integer_step_number(self, tmp_path: Path) -> None:
        path = edited(tmp_path, lambda body: body["steps"][0].update(step="one"))
        with pytest.raises(ReplayError, match="non-integer step number"):
            load(path)
    def test_a_step_that_is_not_an_object(self, tmp_path: Path) -> None:
        path = edited(tmp_path, lambda body: body["steps"].__setitem__(0, "nope"))
        with pytest.raises(ReplayError, match="is not an object"):
            load(path)
    def test_a_commitment_that_is_not_a_string(self, tmp_path: Path) -> None:
        path = edited(tmp_path, lambda body: body["steps"][0].update(commit=42))
        with pytest.raises(ReplayError, match="has no commitment"):
            load(path)
