from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_tamper_acceptance")).items() if not k.startswith("__")})

class TestWhatOneSidedVerificationCannotSee:
    def test_a_truncated_tail_still_stamps_verified_ok(self, tmp_path: Path) -> None:
        def edit(body: dict[str, Any]) -> None:
            body["steps"] = body["steps"][:2]
        assert stamp_after(tmp_path, edit) is Stamp.VERIFIED_OK
    def test_it_is_indistinguishable_from_a_short_match(self, tmp_path: Path) -> None:
        path = honest_log(tmp_path)
        truncated = json.loads(path.read_text())
        truncated["steps"] = truncated["steps"][:2]
        short = json.loads(honest_log(tmp_path / "short", steps=2).read_text())
        assert truncated["steps"] == short["steps"]
    def test_a_step_removed_from_the_middle_leaves_a_visible_gap(self, tmp_path: Path) -> None:
        def edit(body: dict[str, Any]) -> None:
            del body["steps"][1]
        path = by_hand(honest_log(tmp_path), edit)
        replay = load(path)
        assert walk(replay).stamp is Stamp.VERIFIED_OK
        assert replay.numbers() == [1, 3, 4], "the missing number is on the record"
