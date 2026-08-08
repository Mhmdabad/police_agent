from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_match_log")).items() if not k.startswith("__")})

class TestAppendOnly:
    @pytest.mark.parametrize("slot", SLOTS)
    def test_no_slot_can_be_written_twice(self, slot: str) -> None:
        written = played(1)
        actions = {
            "commit": lambda: written.commit(1, "b" * 64),
            "reveal": lambda: written.reveal(1, {**OPENED, "move": "S"}),
            "nonce": lambda: written.disclose(1, "1" * 32),
        }
        with pytest.raises(MatchLogError, match="append-only"):
            actions[slot]()
    def test_an_earlier_step_is_untouched_by_a_later_one(self) -> None:
        written = played(3)
        assert written.entries[1].reveal == OPENED
        assert sorted(written.entries) == [1, 2, 3]
    def test_a_refused_write_leaves_the_original_in_place(self) -> None:
        written = played(1)
        with pytest.raises(MatchLogError):
            written.reveal(1, {**OPENED, "move": "S"})
        assert written.entries[1].reveal == OPENED
