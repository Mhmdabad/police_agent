from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_match")).items() if not k.startswith("__")})

class TestTheConfigItLocks:
    def test_one_per_sub_game(self, tmp_path: Path) -> None:
        runner = a_runner(tmp_path)
        assert runner.config_for(2).sub_game == 2
    def test_it_names_both_teams(self, tmp_path: Path) -> None:
        locked = a_runner(tmp_path).config_for(1)
        assert set(locked.agreed_between) == {"uoh26-cops", "uoh26-others"}
    def test_it_carries_the_shared_uid(self, tmp_path: Path) -> None:
        assert a_runner(tmp_path).config_for(1).game_uid == "u-0001"
