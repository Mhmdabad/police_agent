from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_config_agreement")).items() if not k.startswith("__")})

class TestMatchingConfigsOpenTheSeries:
    def test_both_sides_come_back_with_the_same_digest(self, wire: tuple[Side, Side]) -> None:
        done = both_run(wire, parameters(), parameters())
        assert done == {"ours": agreed_digest(), "theirs": agreed_digest()}
    def test_each_side_consumed_the_others_digest(self, wire: tuple[Side, Side]) -> None:
        ours, theirs = wire
        both_run(wire, parameters(), parameters())
        assert ours.inboxes.digests.empty(), "we never read what the opponent sent"
        assert theirs.inboxes.digests.empty(), "the opponent never read what we sent"
    def test_nothing_was_refused_at_either_door(self, wire: tuple[Side, Side]) -> None:
        ours, theirs = wire
        both_run(wire, parameters(), parameters())
        assert ours.inboxes.rejected == []
        assert theirs.inboxes.rejected == []
    def test_the_digest_advertised_is_the_one_being_enforced(self, wire: tuple[Side, Side]) -> None:
        ours, theirs = fresh(wire)
        concurrently({"ours": gate(ours, parameters()), "theirs": gate(theirs, parameters())})
        filed = theirs.inboxes.digests
        assert filed.empty() or filed.get_nowait()["config_sha256"] == agreed_digest()
