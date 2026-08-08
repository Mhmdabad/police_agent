from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_step_zero")).items() if not k.startswith("__")})

class TestReadingTheMemorySize:
    def test_a_platform_without_sysconf_is_unknown(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def missing(_: str) -> int:
            raise ValueError("unrecognised configuration name")
        monkeypatch.setattr(os, "sysconf", missing)
        assert _ram_mb() is None
    def test_it_reports_megabytes_where_it_can(self) -> None:
        size = _ram_mb()
        assert size is None or size > 0
