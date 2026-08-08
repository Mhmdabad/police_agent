from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_step_zero")).items() if not k.startswith("__")})

class TestReadingTheCpuFrequency:
    def test_it_converts_khz_to_mhz(self, tmp_path: Path) -> None:
        path = tmp_path / "cpuinfo_max_freq"
        path.write_text("3600000\n")
        assert _cpu_max_mhz(path) == 3600.0
    def test_an_absent_file_is_unknown_rather_than_an_error(self, tmp_path: Path) -> None:
        assert _cpu_max_mhz(tmp_path / "nope") is None
    def test_unreadable_contents_are_unknown(self, tmp_path: Path) -> None:
        path = tmp_path / "cpuinfo_max_freq"
        path.write_text("not a number")
        assert _cpu_max_mhz(path) is None
