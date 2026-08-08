from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_main")).items() if not k.startswith("__")})

class TestPlayRefusesWithoutAPublicAddress:
    def test_no_tunnel_stops_it_before_the_handshake(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(REPO)
        assert main(["play", "--game-id", "uoh26-x"], environ=NO_TUNNEL) == 1
    def test_the_message_explains_the_cost_to_both_sides(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.chdir(REPO)
        monkeypatch.setattr("cop_agent.__main__.read_ngrok_api", None)
        main(["play", "--game-id", "uoh26-x"], environ=NO_TUNNEL)
        error = capsys.readouterr().err
        assert "start a tunnel" in error.lower()
        assert "zero for both sides" in error
    def test_a_public_url_gets_it_through(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(REPO)
        started: list[object] = []
        monkeypatch.setattr("cop_agent.__main__.play", record_play(started))
        assert (
            main(
                ["play", "--game-id", "uoh26-x"],
                environ={"PUBLIC_URL": "https://abc.ngrok.io"},
            )
            == 0
        )
        assert started
    def test_serve_still_runs_without_one(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(REPO)
        monkeypatch.setattr("cop_agent.__main__.serve", lambda *_: None)
        assert main([], environ=NO_TUNNEL) == 0
