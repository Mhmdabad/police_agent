from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_rehandshake_between_subgames")).items() if not k.startswith("__")})

class TestTheSeriesReHandshakesAtEveryBoundaryAndNowhereElse:
    def test_a_whole_series_interleaves_one_re_handshake_between_each_pair(
        self, tmp_path: Path, stub: Install
    ) -> None:
        stub()
        transport = ScriptedPeer(PeerInboxes())
        runner = opened(tmp_path, transport)
        runner.play_series(timeout=1.0)
        assert transport.tools == ["negotiate"] + ["receive_turn", "negotiate"] * 5 + [
            "receive_turn"
        ]
    def test_the_opening_handshake_happens_once_and_before_the_first_sub_game(
        self, tmp_path: Path, stub: Install
    ) -> None:
        stub()
        transport = ScriptedPeer(PeerInboxes())
        runner = opened(tmp_path, transport)
        assert transport.tools == ["negotiate"]
        runner.play_series(timeout=1.0)
        assert transport.tools[0] == "negotiate"
    def test_nothing_re_handshakes_after_the_last_sub_game(
        self, tmp_path: Path, stub: Install
    ) -> None:
        stub()
        transport = ScriptedPeer(PeerInboxes())
        runner = opened(tmp_path, transport)
        runner.play_series(timeout=1.0)
        assert transport.tools[-1] == "receive_turn"
        assert transport.tools.count("negotiate") == 1 + len(BOUNDARIES)
    def test_the_boundary_is_agreed_for_the_sub_game_it_precedes(
        self, tmp_path: Path, stub: Install
    ) -> None:
        stub()
        transport = ScriptedPeer(PeerInboxes())
        runner = opened(tmp_path, transport)
        agreed: list[int] = []
        original = MatchRunner.rehandshake
        def watched(
            self: MatchRunner, number: int, timeout: float = GREETING_TIMEOUT_SEC
        ) -> Peering:
            later = original(self, number, timeout)
            agreed.append(later.sub_game)
            return later
        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(MatchRunner, "rehandshake", watched)
            runner.play_series(timeout=1.0)
        assert agreed == BOUNDARIES
        assert runner.peering is not None and runner.peering.sub_game == BOOK_SERIES
    def test_every_sub_game_of_the_book_series_was_played(
        self, tmp_path: Path, stub: Install
    ) -> None:
        stub()
        transport = ScriptedPeer(PeerInboxes())
        runner = opened(tmp_path, transport)
        assert [o.number for o in runner.play_series(timeout=1.0)] == list(range(1, 7))
    def test_a_series_that_never_traded_addresses_refuses_to_open(
        self, tmp_path: Path, stub: Install
    ) -> None:
        stub()
        transport = ScriptedPeer(PeerInboxes())
        runner = a_runner(tmp_path, transport, peering=None)
        with pytest.raises(MatchAborted) as excinfo:
            runner.play_series(timeout=1.0)
        assert excinfo.value.cause is TechnicalLoss.ILLEGAL_ACTION
        assert runner.outcomes == []
