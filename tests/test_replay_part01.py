from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_replay")).items() if not k.startswith("__")})

class TestItLoadsWhatTheWriterWrote:
    def test_a_real_log_round_trips(self, tmp_path: Path) -> None:
        replay = load(written(tmp_path))
        assert replay.numbers() == [1, 2, 3, 4]
        assert replay.game_id == "uoh26-s82kma9e"
        assert replay.sub_game == 2
        assert replay.role == "police"
    def test_each_step_carries_its_three_slots(self, tmp_path: Path) -> None:
        first = load(written(tmp_path)).current
        assert first.step == 1
        assert first.commit == f"{1:064x}"
        assert first.reveal == OPENED
        assert first.openable
    def test_a_step_with_no_nonce_is_loaded_and_flagged(self, tmp_path: Path) -> None:
        replay = load(written(tmp_path, unopened=2))
        assert replay.seek(4).nonce is None
        assert not replay.seek(4).openable
        assert replay.seek(1).openable
