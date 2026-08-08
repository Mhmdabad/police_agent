from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_stage5_remote")).items() if not k.startswith("__")})

class TestConfiguringTheRemotePeer:
    def test_the_committed_config_is_overridden_for_league_play(self) -> None:
        local = ClientSettings.from_config({"opponent_url": "http://127.0.0.1:8802/mcp"}, {})
        remote = ClientSettings.from_config(
            {"opponent_url": "http://127.0.0.1:8802/mcp"}, {OPPONENT_URL_ENV: THIEF_URL}
        )
        assert local.opponent_url == "http://127.0.0.1:8802/mcp"
        assert remote.opponent_url == THIEF_URL
