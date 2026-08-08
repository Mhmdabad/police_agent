from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_token_store")).items() if not k.startswith("__")})

class TestEveryRefusalSaysHowToFixIt:
    @pytest.mark.parametrize(
        "overrides",
        [
            {"scopes": [SEND_SCOPE, READ_SCOPE]},
            {"refresh_token": ""},
            {"client_id": OTHER},
        ],
    )
    def test_it_names_the_command_to_run(self, tmp_path: Path, overrides: dict[str, Any]) -> None:
        with pytest.raises(TokenError, match="infra.authorize"):
            read(stored(tmp_path, **overrides), CLIENT)
    def test_it_warns_about_the_seven_day_expiry(self, tmp_path: Path) -> None:
        with pytest.raises(TokenError, match="seven days"):
            read(tmp_path / "token_cop.json", CLIENT)
    def test_the_module_named_matches_the_package(self, tmp_path: Path) -> None:
        with pytest.raises(TokenError, match="cop_agent.infra.authorize"):
            read(tmp_path / "token_cop.json", CLIENT, package="cop_agent")
