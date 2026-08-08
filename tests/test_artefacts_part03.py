from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_artefacts")).items() if not k.startswith("__")})

class TestTheGameIdMustMatchToo:
    def test_a_config_from_another_match(self) -> None:
        other = a_config(1, game_id="uoh26-other")
        assert "not 'uoh26-s82kma9e'" in str(a_set(configs=(other, a_config(2))).check())
    def test_a_log_from_another_match(self) -> None:
        other = a_log(1, game_id="uoh26-other")
        assert "log g01 is for game" in str(a_set(logs=(other, a_log(2))).check())
    def test_a_result_from_another_match(self) -> None:
        assert "the result is for game" in str(
            a_set(result=a_result(game_id="uoh26-other")).check()
        )
