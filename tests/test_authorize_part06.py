from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_authorize")).items() if not k.startswith("__")})

class TestTheCommandLine:
    def test_a_successful_run_exits_zero(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        client_file(tmp_path)
        monkeypatch.setattr(
            "cop_agent.infra.authorize.google_flow", returning(GRANTED), raising=True
        )
        assert main([str(tmp_path / CREDENTIALS_FILE)]) == 0
    def test_a_failure_exits_one_rather_than_raising(self, tmp_path: Path) -> None:
        assert main([str(tmp_path / "absent.json")]) == 1
    def test_it_defaults_to_credentials_json_in_the_working_directory(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        assert main([]) == 1, "no credentials.json here, so it should fail cleanly"
    def test_it_reads_sys_argv_when_given_nothing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("sys.argv", ["authorize", str(tmp_path / "absent.json")])
        assert main() == 1
    def test_the_failure_is_reported_on_stderr(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        main([str(tmp_path / "absent.json")])
        assert "authorization failed" in capsys.readouterr().err
