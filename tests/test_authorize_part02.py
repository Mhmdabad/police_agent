from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_authorize")).items() if not k.startswith("__")})

class TestTheClientIsCheckedBeforeTheBrowserOpens:
    def test_a_web_client_is_refused_without_running_the_flow(self, tmp_path: Path) -> None:
        seen: list[Any] = []
        with pytest.raises(CredentialsError, match="Web application"):
            authorize(
                client_file(tmp_path, {"web": DESKTOP["installed"]}),
                tmp_path / "t.json",
                returning(GRANTED, seen),
            )
        assert seen == [], "the flow ran before the client file was judged"
    def test_a_missing_client_file_is_refused_without_running_the_flow(
        self, tmp_path: Path
    ) -> None:
        seen: list[Any] = []
        with pytest.raises(CredentialsError):
            authorize(tmp_path / CREDENTIALS_FILE, tmp_path / "t.json", returning(GRANTED, seen))
        assert seen == []
