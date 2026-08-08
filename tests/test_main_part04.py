from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_main")).items() if not k.startswith("__")})

class TestServing:
    def test_it_starts_the_server_with_the_configured_settings(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(REPO)
        started: list[object] = []
        monkeypatch.setattr(
            "cop_agent.__main__.serve", lambda host, settings: started.append(settings)
        )
        assert main([], environ=NO_TUNNEL) == 0
        assert len(started) == 1
        assert getattr(started[0], "port", None) == 8801
    def test_serve_is_the_default_command(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(REPO)
        started: list[object] = []
        monkeypatch.setattr("cop_agent.__main__.serve", lambda *_: started.append(True))
        main([], environ=NO_TUNNEL)
        assert started, "no argument should mean serve"
    def test_it_reads_the_real_environment_when_none_is_given(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(REPO)
        monkeypatch.delenv("PUBLIC_URL", raising=False)
        monkeypatch.setattr("cop_agent.__main__.serve", lambda *_: None)
        assert main([]) == 0
