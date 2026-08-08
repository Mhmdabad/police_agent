from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_rehandshake_between_subgames")).items() if not k.startswith("__")})

class TestABoundaryFailsClosedOnTheAppendixFDeadline:
    def refusing(
        self, tmp_path: Path, stub: Install, announce: dict[str, Any] | None, at: int = 1
    ) -> MatchAborted:
        transport = ScriptedPeer(PeerInboxes())
        def swap(played: int) -> None:
            if played == at:
                transport.announce = announce
        stub(swap)
        runner = opened(tmp_path, transport)
        with pytest.raises(MatchAborted) as excinfo:
            runner.play_series(timeout=0.05)
        assert runner.orchestrator.client.opponent_url == AT_THEIRS
        return excinfo.value
    def test_the_greeting_deadline_is_the_appendix_f_response_timeout(self) -> None:
        assert float(BOOK_RESPONSE_TIMEOUT) == GREETING_TIMEOUT_SEC
    def test_an_opponent_that_never_re_greets_is_a_timeout(
        self, tmp_path: Path, stub: Install
    ) -> None:
        assert self.refusing(tmp_path, stub, None).cause is TechnicalLoss.TIMEOUT
    def test_the_wait_is_bounded_rather_than_open_ended(
        self, tmp_path: Path, stub: Install
    ) -> None:
        started = time.monotonic()
        self.refusing(tmp_path, stub, None)
        assert time.monotonic() - started < 5.0
    @pytest.mark.parametrize(
        "greeting",
        [
            {"greeting": {"role": OPPONENT, "group_id": "them", "public_url": ROTATED}},
            {"greeting": {"role": OPPONENT, "group_id": "them"}},
            {"greeting": "https://thief-e5f6.ngrok-free.app"},
            {"greeting": {"role": OPPONENT, "group_id": "", "public_url": ROTATED}},
            {"greeting": {}},
        ],
        ids=["no-version", "no-address", "not-an-object", "no-group", "empty"],
    )
    def test_a_malformed_greeting_is_refused(
        self, tmp_path: Path, stub: Install, greeting: dict[str, Any]
    ) -> None:
        assert self.refusing(tmp_path, stub, greeting).cause is TechnicalLoss.ILLEGAL_ACTION
    @pytest.mark.parametrize("url", [PRIVATE, LOOPBACK], ids=["private", "loopback"])
    def test_an_address_that_routes_nowhere_is_refused(
        self, tmp_path: Path, stub: Install, url: str
    ) -> None:
        refused = self.refusing(tmp_path, stub, greets(url))
        assert refused.cause is TechnicalLoss.ILLEGAL_ACTION
        assert "routes nowhere" in refused.detail
    def test_a_stale_greeting_for_a_sub_game_already_played_is_refused(
        self, tmp_path: Path, stub: Install
    ) -> None:
        stub()
        transport = ScriptedPeer(PeerInboxes())
        runner = opened(tmp_path, transport)
        runner.play_sub_game(1, timeout=1.0)
        with pytest.raises(MatchAborted, match="only change between sub-games"):
            runner.rehandshake(1, timeout=1.0)
        assert runner.orchestrator.client.opponent_url == AT_THEIRS
    @pytest.mark.parametrize(
        "conflict_first", [True, False], ids=["conflict-first", "conflict-last"]
    )
    def test_two_conflicting_greetings_in_one_window_are_refused_either_way(
        self, tmp_path: Path, stub: Install, conflict_first: bool
    ) -> None:
        transport = ScriptedPeer(PeerInboxes())
        pair = [greets(ROTATED, group_id="someone-else"), greets(ROTATED)]
        def both(played: int) -> None:
            if played != 1:
                return
            transport.announce = None
            for message in pair if conflict_first else list(reversed(pair)):
                transport.inboxes.negotiate(message)
        stub(both)
        runner = opened(tmp_path, transport)
        with pytest.raises(MatchAborted) as excinfo:
            runner.play_series(timeout=1.0)
        assert excinfo.value.cause is TechnicalLoss.ILLEGAL_ACTION
        assert runner.orchestrator.client.opponent_url == AT_THEIRS
    def test_an_identical_duplicate_greeting_is_not_a_conflict(
        self, tmp_path: Path, stub: Install
    ) -> None:
        transport = ScriptedPeer(PeerInboxes())
        def twice(played: int) -> None:
            if played == 1:
                transport.inboxes.negotiate(greets(THEIR_URL))
        stub(twice)
        runner = opened(tmp_path, transport)
        assert len(runner.play_series(timeout=1.0)) == BOOK_SERIES
