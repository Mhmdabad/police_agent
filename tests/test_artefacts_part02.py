from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_artefacts")).items() if not k.startswith("__")})

class TestTheUidMustMatchEverywhere:
    def test_a_config_with_a_different_uid(self) -> None:
        wrong = a_set(configs=(a_config(1), a_config(2, uid="u-9999")))
        assert "config g02 has a different game_uid" in str(wrong.check())
    def test_a_log_with_a_different_uid(self) -> None:
        wrong = a_set(logs=(a_log(1, uid="u-9999"), a_log(2)))
        assert "log g01 has a different game_uid" in str(wrong.check())
    def test_a_result_with_a_different_uid(self) -> None:
        assert "the result has a different game_uid" in str(
            a_set(result=a_result(uid="u-9")).check()
        )
    def test_a_declaration_with_no_uid_at_all(self) -> None:
        with pytest.raises(Exception, match="shares a game_uid"):
            a_declaration(uid="")
    def test_this_is_the_silent_failure(self) -> None:
        wrong = a_set(logs=(a_log(1, uid="u-9999"), a_log(2)))
        assert not wrong.check().coherent
        assert wrong.logs[0].verifiable().complete, "the log itself is fine; the link is wrong"
