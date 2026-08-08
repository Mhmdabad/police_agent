from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_ceremony")).items() if not k.startswith("__")})

class TestReceivingTheirReveal:
    def test_a_locked_pair_may_be_believed(self) -> None:
        ceremony = both_locked()
        theirs = reveal(sender="thief", move="S")
        assert ceremony.receive_reveal(theirs) is ceremony.revealed_theirs
    def test_it_cannot_be_verified_when_it_is_acted_upon(self) -> None:
        ceremony = both_locked()
        theirs = reveal(sender="thief", move="S")
        ceremony.receive_reveal(theirs)
        assert ceremony.theirs is not None
        assert "nonce" not in json.dumps(theirs.to_dict())
    def test_storing_it_is_the_whole_job(self) -> None:
        ceremony = both_locked()
        ceremony.receive_reveal(reveal(sender="thief", move="S", barrier_placed=None))
        assert ceremony.revealed_theirs is not None
        assert ceremony.revealed_theirs.move == "S"
    def test_a_reveal_before_the_lock_is_refused(self) -> None:
        with pytest.raises(CeremonyError, match="before both sides were locked"):
            opened().receive_reveal(reveal(sender="thief"))
    def test_a_second_reveal_from_them_is_refused(self) -> None:
        ceremony = both_locked()
        ceremony.receive_reveal(reveal(sender="thief"))
        with pytest.raises(CeremonyError, match="already revealed"):
            ceremony.receive_reveal(reveal(sender="thief", move="W"))
    def test_their_reveal_must_come_from_them(self) -> None:
        with pytest.raises(CeremonyError, match="expected 'thief'"):
            both_locked().receive_reveal(reveal())
    def test_pending_reads_as_locked_once_it_is(self) -> None:
        assert both_locked().pending() == "locked"
