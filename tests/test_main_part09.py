from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_main")).items() if not k.startswith("__")})

class TestRehearsalIsExemptFromTheTunnelRequirement:
    def test_rehearsing_announces_to_nobody_so_the_refusal_does_not_apply(self) -> None:
        require_playable(argparse.Namespace(game_id="uoh26-x", rehearse=True), NO_TUNNEL, NO_NGROK)
    def test_rehearsing_does_not_excuse_a_missing_game_id(self) -> None:
        with pytest.raises(StartupError, match="game-id"):
            require_playable(argparse.Namespace(game_id="", rehearse=True), NO_TUNNEL, NO_NGROK)
    def test_without_the_flag_a_tunnel_is_still_required(self) -> None:
        with pytest.raises(StartupError, match="Start a tunnel"):
            require_playable(argparse.Namespace(game_id="uoh26-x", rehearse=False), {}, NO_NGROK)
