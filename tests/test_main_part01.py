from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_main")).items() if not k.startswith("__")})

class TestCheckReportsWithoutBinding:
    def test_it_exits_zero(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(REPO)
        assert main(["check"], environ=NO_TUNNEL) == 0
    def test_it_names_this_agent_and_its_role(self, capsys: pytest.CaptureFixture[str]) -> None:
        lines = describe(private(), NO_TUNNEL)
        assert lines[0] == "cop-agent (police)"
    def test_it_reports_the_port_it_would_listen_on(self) -> None:
        assert "8801" in describe(private(), NO_TUNNEL)[1]
    def test_it_reports_the_opponent(self) -> None:
        assert "8802" in describe(private(), NO_TUNNEL)[3]
    def test_it_lists_the_four_tools(self) -> None:
        tools = describe(private(), NO_TUNNEL)[4]
        for name in ("negotiate", "receive_turn", "submit_audit", "receive_control"):
            assert name in tools
    def test_nothing_is_bound(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(REPO)
        monkeypatch.setattr(
            "cop_agent.__main__.serve",
            lambda *_: pytest.fail("check must not start a server"),
        )
        assert main(["check"], environ=NO_TUNNEL) == 0
