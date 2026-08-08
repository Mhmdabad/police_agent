from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_scent_lock_negotiation")).items() if not k.startswith("__")})

class TestTwoHonestPeersLockTheSameModel:
    def test_both_sides_come_back_with_the_same_agreement(self, wire: tuple[Side, Side]) -> None:
        assert both_lock(wire) == {"ours": our_lock(), "theirs": our_lock()}
    def test_the_agreement_carries_the_digest_of_the_model(self, wire: tuple[Side, Side]) -> None:
        assert both_lock(wire)["ours"].digest == propose().digest()
    def test_each_side_consumed_the_others_offer(self, wire: tuple[Side, Side]) -> None:
        ours, theirs = wire
        both_lock(wire)
        assert ours.inboxes.scent_locks.empty(), "we never read what the opponent sent"
        assert theirs.inboxes.scent_locks.empty(), "the opponent never read what we sent"
    def test_nothing_was_refused_at_either_door(self, wire: tuple[Side, Side]) -> None:
        ours, theirs = wire
        both_lock(wire)
        assert ours.inboxes.rejected == []
        assert theirs.inboxes.rejected == []
    def test_the_digest_advertised_covers_the_model_sent(self, wire: tuple[Side, Side]) -> None:
        ours, theirs = fresh(wire)
        with pytest.raises(MatchAborted):
            ours.orchestrator.agree_scent_model(game_uid=GAME_UID, timeout=BRIEF)
        filed = theirs.inboxes.scent_locks.get_nowait()
        assert restate(filed[SCENT_KEY]) == filed[SCENT_DIGEST_KEY] == propose().digest()
    def test_the_source_offer_travels_with_it(self, wire: tuple[Side, Side]) -> None:
        ours, theirs = fresh(wire)
        with pytest.raises(MatchAborted):
            ours.orchestrator.agree_scent_model(game_uid=GAME_UID, timeout=BRIEF)
        offered = theirs.inboxes.scent_locks.get_nowait()[SCENT_KEY]
        assert "domain/scent.py" in str(offered["source_offer"])
