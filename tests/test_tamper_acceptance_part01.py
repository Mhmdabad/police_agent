from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_tamper_acceptance")).items() if not k.startswith("__")})

class TestTheDetectorIsNotSimplyAlwaysRed:
    def test_an_untouched_log_stamps_verified_ok(self, tmp_path: Path) -> None:
        result = walk(load(honest_log(tmp_path)))
        assert result.stamp is Stamp.VERIFIED_OK
        assert result.verified == STEPS
    def test_a_log_rewritten_without_changes_still_stamps_clean(self, tmp_path: Path) -> None:
        assert stamp_after(tmp_path, lambda body: None) is Stamp.VERIFIED_OK
