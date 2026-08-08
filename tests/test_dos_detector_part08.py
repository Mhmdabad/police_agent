from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_dos_detector")).items() if not k.startswith("__")})

class TestWhereTheLockLives:
    def test_it_is_named_per_agent(self) -> None:
        assert lock_path("cop_agent", {}).name == ".locked_cop.json"
        assert lock_path("thief_agent", {}).name == ".locked_thief.json"
    def test_the_environment_overrides_it(self) -> None:
        assert lock_path("cop_agent", {LOCK_PATH_ENV: "/tmp/l.json"}) == Path("/tmp/l.json")
    def test_it_reads_the_real_environment_when_none_is_given(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(LOCK_PATH_ENV, "/tmp/from-env.json")
        assert lock_path("cop_agent") == Path("/tmp/from-env.json")
