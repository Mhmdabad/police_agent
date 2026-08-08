from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_localhost_match")).items() if not k.startswith("__")})

class TestBothLogsVerify:
    def test_the_cops_log_stamps_verified_ok(self, played: tuple[Side, Side, Path]) -> None:
        cop, _, where = played
        result = walk(load(played_log(cop).write(where / "cop")))
        assert result.stamp is Stamp.VERIFIED_OK, str(result)
    def test_the_thiefs_log_stamps_verified_ok(self, played: tuple[Side, Side, Path]) -> None:
        _, thief, where = played
        result = walk(load(played_log(thief).write(where / "thief")))
        assert result.stamp is Stamp.VERIFIED_OK, str(result)
    def test_both_are_fully_re_verifiable(self, played: tuple[Side, Side, Path]) -> None:
        cop, thief, _ = played
        assert played_log(cop).verifiable().complete
        assert played_log(thief).verifiable().complete
    def test_no_nonce_left_early(self, played: tuple[Side, Side, Path]) -> None:
        cop, thief, _ = played
        assert played_log(cop).unopened() == []
        assert played_log(thief).unopened() == []
