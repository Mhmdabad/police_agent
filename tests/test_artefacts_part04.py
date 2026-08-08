from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_artefacts")).items() if not k.startswith("__")})

class TestHolesInTheEvidence:
    def test_a_config_with_no_log(self) -> None:
        thin = a_set(logs=(a_log(1),), result=a_result(sub_games=(1,)))
        assert "sub-game 2 has a config but no log" in str(thin.check())
    def test_a_log_with_no_config(self) -> None:
        thin = a_set(configs=(a_config(1),))
        assert "sub-game 2 has a log but no config" in str(thin.check())
    def test_a_result_reporting_a_sub_game_that_was_never_played(self) -> None:
        assert "reports sub-game 3, which has no log" in str(
            a_set(result=a_result((1, 2, 3))).check()
        )
    def test_a_played_sub_game_missing_from_the_result(self) -> None:
        assert "sub-game 2 was played but is not in the result" in str(
            a_set(result=a_result((1,))).check()
        )
    def test_two_configs_for_one_sub_game(self) -> None:
        assert "two configs claim the same sub-game" in str(
            a_set(configs=(a_config(1), a_config(1))).check()
        )
    def test_two_logs_for_one_sub_game(self) -> None:
        assert "two logs claim the same sub-game" in str(a_set(logs=(a_log(1), a_log(1))).check())
