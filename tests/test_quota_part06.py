from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_quota")).items() if not k.startswith("__")})

class TestWhereTheLedgerLives:
    def test_it_is_named_per_agent(self) -> None:
        assert quota_path("cop_agent", {}).name == ".quota_cop.json"
        assert quota_path("thief_agent", {}).name == ".quota_thief.json"
    def test_the_environment_overrides_it(self) -> None:
        assert quota_path("cop_agent", {QUOTA_PATH_ENV: "/tmp/q.json"}) == Path("/tmp/q.json")
    def test_it_reads_the_real_environment_when_none_is_given(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(QUOTA_PATH_ENV, "/tmp/from-env.json")
        assert quota_path("cop_agent") == Path("/tmp/from-env.json")
