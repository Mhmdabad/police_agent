from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_verdict")).items() if not k.startswith("__")})

class TestACleanLogIsStamped:
    def test_it_stamps_verified_ok(self, tmp_path: Path) -> None:
        result = walk(load(sealed_log(tmp_path)))
        assert result.stamp is Stamp.VERIFIED_OK
        assert result.stamp.text == "Verified OK"
        assert result.clean and not result.void
    def test_it_reports_every_step_as_re_derived(self, tmp_path: Path) -> None:
        result = walk(load(sealed_log(tmp_path, steps=6)))
        assert (result.verified, result.total) == (6, 6)
        assert result.at_step is None
    def test_the_stamp_is_green(self, tmp_path: Path) -> None:
        assert walk(load(sealed_log(tmp_path))).stamp.value == "green"
    def test_it_reads_as_a_sentence(self, tmp_path: Path) -> None:
        assert str(walk(load(sealed_log(tmp_path)))) == "Verified OK — 4 steps re-derived"
