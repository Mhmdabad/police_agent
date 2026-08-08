from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_tamper_acceptance")).items() if not k.startswith("__")})

class TestRearrangingRatherThanEditing:
    def test_swapping_two_commitments(self, tmp_path: Path) -> None:
        def edit(body: dict[str, Any]) -> None:
            first, second = body["steps"][0], body["steps"][1]
            first["commit"], second["commit"] = second["commit"], first["commit"]
        assert stamp_after(tmp_path, edit) is Stamp.TAMPERED
    def test_swapping_two_nonces(self, tmp_path: Path) -> None:
        def edit(body: dict[str, Any]) -> None:
            first, second = body["steps"][0], body["steps"][1]
            first["nonce"], second["nonce"] = second["nonce"], first["nonce"]
        assert stamp_after(tmp_path, edit) is Stamp.TAMPERED
    def test_replaying_a_whole_earlier_step_under_a_later_number(self, tmp_path: Path) -> None:
        def edit(body: dict[str, Any]) -> None:
            copied = deepcopy(body["steps"][0])
            copied["step"] = 3
            body["steps"][2] = copied
        result = walk(load(by_hand(honest_log(tmp_path), edit)))
        assert result.stamp is Stamp.TAMPERED
        assert result.at_step == 3
        assert "seals step 1" in result.reason
    def test_the_copied_row_re_derives_on_its_own(self, tmp_path: Path) -> None:
        def edit(body: dict[str, Any]) -> None:
            copied = deepcopy(body["steps"][0])
            copied["step"] = 3
            body["steps"][2] = copied
        row = load(by_hand(honest_log(tmp_path), edit)).seek(3)
        assert row.reveal is not None and row.nonce is not None
        assert commit_of(row.reveal, row.nonce) == row.commit
