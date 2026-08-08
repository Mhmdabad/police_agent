from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_token_store")).items() if not k.startswith("__")})

class TestWhereTheTokenLives:
    def test_it_is_named_per_agent_not_token_json(self) -> None:
        assert token_path("cop_agent", {}).name == "token_cop.json"
        assert token_path("thief_agent", {}).name == "token_thief.json"
    def test_the_environment_overrides_it(self) -> None:
        chosen = token_path("cop_agent", {TOKEN_PATH_ENV: "/secure/elsewhere.json"})
        assert chosen == Path("/secure/elsewhere.json")
    def test_it_reads_the_real_environment_when_none_is_given(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(TOKEN_PATH_ENV, "/tmp/from-env.json")
        assert token_path("cop_agent") == Path("/tmp/from-env.json")
