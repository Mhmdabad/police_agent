from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_stage6_acceptance")).items() if not k.startswith("__")})

class TestAnHonestMatchAuditsClean:
    def test_each_side_re_derives_the_other(self) -> None:
        game = play()
        for match, disclosure in (
            (game.cop.match, game.thief_disclosure),
            (game.thief.match, game.cop_disclosure),
        ):
            result = audit_opponent(match, disclosure, game.states)
            assert result.clean
            assert result.checked == STEPS
    def test_the_log_is_complete(self) -> None:
        game = play()
        assert game.cop.log.unopened() == []
        assert len(game.cop.log.entries) == STEPS
    def test_the_log_records_commit_before_reveal_for_every_step(self) -> None:
        for entry in play().cop.log.entries.values():
            assert entry.commit and entry.reveal and entry.nonce
