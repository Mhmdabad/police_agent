from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_main")).items() if not k.startswith("__")})

class TestItFailsWithAReasonRatherThanATraceback:
    def test_a_missing_config_exits_one(self, tmp_path: Path) -> None:
        assert main(["check", "--config", str(tmp_path / "absent.toml")], environ=NO_TUNNEL) == 1
    def test_the_missing_config_message_says_where_to_run_it(self, tmp_path: Path) -> None:
        with pytest.raises(StartupError, match="repository root"):
            load_private(tmp_path / "absent.toml")
    def test_an_unreadable_config_is_named(self, tmp_path: Path) -> None:
        (tmp_path / "broken.toml").write_text("this is not = = toml")
        with pytest.raises(StartupError, match="cannot read"):
            load_private(tmp_path / "broken.toml")
    def test_a_directory_in_place_of_the_config(self, tmp_path: Path) -> None:
        (tmp_path / "dir.toml").mkdir()
        with pytest.raises(StartupError, match="cannot read"):
            load_private(tmp_path / "dir.toml")
    def test_a_config_with_no_network_section_exits_one(self, tmp_path: Path) -> None:
        (tmp_path / "thin.toml").write_text('version = "1.0"\n')
        assert main(["check", "--config", str(tmp_path / "thin.toml")], environ=NO_TUNNEL) == 1
    def test_the_failure_goes_to_stderr(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        main(["check", "--config", str(tmp_path / "absent.toml")], environ=NO_TUNNEL)
        assert "cannot start" in capsys.readouterr().err
    def test_a_bad_public_url_stops_it_before_the_socket(self, tmp_path: Path) -> None:
        assert main(["check"], environ={"PUBLIC_URL": "http://127.0.0.1:1"}) == 1
