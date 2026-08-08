from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_replay")).items() if not k.startswith("__")})

class TestStructureIsNotHonesty:
    def test_a_tampered_but_well_formed_log_loads_fine(self, tmp_path: Path) -> None:
        path = edited(tmp_path, lambda body: body["steps"][1].update(commit="f" * 64))
        replay = load(path)
        assert replay.numbers() == [1, 2, 3, 4]
        assert replay.seek(2).commit == "f" * 64
    def test_loading_says_nothing_about_verification(self, tmp_path: Path) -> None:
        assert not hasattr(load(written(tmp_path)), "verdict")
