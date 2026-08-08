from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_rehandshake_between_subgames")).items() if not k.startswith("__")})

class TestAnUnchangedAddressIsAcceptedIdempotently:
    def test_six_sub_games_on_one_address_re_point_nothing(
        self, tmp_path: Path, stub: Install
    ) -> None:
        stub()
        transport = ScriptedPeer(PeerInboxes())
        runner = opened(tmp_path, transport)
        runner.play_series(timeout=1.0)
        assert transport.where("receive_turn") == [AT_THEIRS] * BOOK_SERIES
        assert runner.orchestrator.client.relocations == []
    def test_the_boundaries_still_happened(self, tmp_path: Path, stub: Install) -> None:
        stub()
        transport = ScriptedPeer(PeerInboxes())
        runner = opened(tmp_path, transport)
        runner.play_series(timeout=1.0)
        assert transport.tools.count("negotiate") == 1 + len(BOUNDARIES)
    def test_no_relocation_is_reported_for_an_address_that_did_not_move(
        self, tmp_path: Path, stub: Install
    ) -> None:
        stub()
        transport = ScriptedPeer(PeerInboxes())
        runner = opened(tmp_path, transport)
        runner.play_series(timeout=1.0)
        assert not [b for b in runner.orchestrator.heartbeats if b.startswith("agreed-move:")]
