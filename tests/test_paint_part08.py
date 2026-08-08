from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_paint")).items() if not k.startswith("__")})

class TestTheCommandLine:
    def test_replay_without_a_log_is_refused(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert main(["replay"]) == 1
        assert "needs a log file" in capsys.readouterr().err
    def test_replay_opens_the_named_log(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        opened: list[Path] = []
        def record(path: Path) -> int:
            opened.append(path)
            return 0
        monkeypatch.setattr("cop_agent.ui.app.run_replay", record)
        log = sealed_log(tmp_path)
        assert main(["replay", str(log)]) == 0
        assert opened == [log]
    def test_live_needs_no_argument(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("cop_agent.ui.app.run_live", lambda _: 0)
        assert main(["live"]) == 0
    def test_an_unknown_window_is_rejected_by_the_parser(self) -> None:
        with pytest.raises(SystemExit):
            main(["sideways"])
