from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_match_log")).items() if not k.startswith("__")})

class TestTheOrderIsTheEvidence:
    def test_a_full_step_records_all_three_slots(self) -> None:
        assert tuple(played(1).entries[1].to_dict()) == ("step", *SLOTS, "discussion")
    def test_a_reveal_before_a_commitment_is_refused(self) -> None:
        with pytest.raises(MatchLogError, match="no commitment recorded"):
            log().reveal(1, OPENED)
    def test_a_nonce_before_a_reveal_is_refused(self) -> None:
        written = log()
        written.commit(1, DIGEST)
        with pytest.raises(MatchLogError, match="no reveal to open"):
            written.disclose(1, NONCE)
    def test_the_three_slots_fill_in_order_without_complaint(self) -> None:
        written = log()
        written.commit(1, DIGEST)
        written.reveal(1, OPENED)
        written.disclose(1, NONCE)
        assert written.entries[1].nonce == NONCE
