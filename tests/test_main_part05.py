from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_main")).items() if not k.startswith("__")})

class TestPlayRefusesWithoutAnAgreedGameId:
    def test_play_without_a_game_id_exits_one(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(REPO)
        assert main(["play"], environ=NO_TUNNEL) == 1
    def test_the_message_says_it_must_be_agreed_beforehand(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.chdir(REPO)
        main(["play"], environ=NO_TUNNEL)
        assert "agreed with the opponent" in capsys.readouterr().err
    def test_a_game_id_gets_it_past_the_check(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(REPO)
        started: list[object] = []
        monkeypatch.setattr("cop_agent.__main__.play", record_play(started))
        assert (
            main(["play", "--game-id", "uoh26-test"], environ={"PUBLIC_URL": "https://a.ngrok.io"})
            == 0
        )
        assert started, "play was never reached"
