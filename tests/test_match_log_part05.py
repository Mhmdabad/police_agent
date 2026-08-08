from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_match_log")).items() if not k.startswith("__")})

class TestTheDiscussionFields:
    def test_they_are_recorded(self) -> None:
        log = MatchLog(game_id="uoh26-s82kma9e", sub_game=1, role="police")
        log.commit(1, "a" * 64)
        log.discuss(1, {"prompt_tokens": 120, "reasoning": "close the north gap"})
        assert log.entries[1].discussion == {
            "prompt_tokens": 120,
            "reasoning": "close the north gap",
        }
    def test_they_are_write_once_like_everything_else(self) -> None:
        log = MatchLog(game_id="uoh26-s82kma9e", sub_game=1, role="police")
        log.commit(1, "a" * 64)
        log.discuss(1, {"reasoning": "first"})
        with pytest.raises(MatchLogError, match="already has a discussion"):
            log.discuss(1, {"reasoning": "second"})
    def test_they_cannot_precede_the_commitment(self) -> None:
        log = MatchLog(game_id="uoh26-s82kma9e", sub_game=1, role="police")
        with pytest.raises(MatchLogError, match="before any commitment"):
            log.discuss(1, {"reasoning": "I intend to"})
    def test_they_are_not_one_of_the_committed_slots(self) -> None:
        assert "discussion" not in SLOTS
    def test_a_log_is_verifiable_without_them(self) -> None:
        log = sealed_log()
        assert log.verifiable().complete
        assert log.entries[1].discussion is None
