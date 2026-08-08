from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_verdict")).items() if not k.startswith("__")})

class TestTheVerdictDoesNotReadEnglish:
    def test_a_record_that_cannot_be_hashed_at_all_is_tampered(self, tmp_path: Path) -> None:
        path = sealed_log(tmp_path)
        def edit(body: dict[str, Any]) -> None:
            body["steps"][0]["reveal"]["nonce"] = "deadbeef"
        result = walk(load(hand_edited(path, edit)))
        assert result.stamp is Stamp.TAMPERED
        assert result.at_step == 1
        assert "cannot be hashed as the committer hashed it" in result.reason
    def test_check_step_answers_rather_than_raising(self, tmp_path: Path) -> None:
        path = sealed_log(tmp_path)
        def edit(body: dict[str, Any]) -> None:
            body["steps"][0]["reveal"]["nonce"] = "deadbeef"
        checked = check_step(load(hand_edited(path, edit)).current)
        assert not checked.verified
    def test_the_split_is_openable_not_the_wording_of_a_reason(self, tmp_path: Path) -> None:
        forged = walk(load(sealed_log(tmp_path, corrupt=1)))
        partial = walk(load(sealed_log(tmp_path / "b", unopened=4)))
        assert forged.reason and partial.reason
        assert forged.void and not partial.void
