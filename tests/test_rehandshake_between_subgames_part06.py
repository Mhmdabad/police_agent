from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_rehandshake_between_subgames")).items() if not k.startswith("__")})

class TestATransientAnnounceFailureCannotHangOrSkipABoundary:
    def failing_boundary(self, tmp_path: Path, stub: Install) -> tuple[MatchRunner, ScriptedPeer]:
        budget = BOOK_RETRIES + 1
        transport = ScriptedPeer(PeerInboxes(), failing=frozenset(range(2, 2 + budget)))
        def rotate(played: int) -> None:
            if played == 1:
                transport.announce = greets(ROTATED)
        stub(rotate)
        runner = opened(tmp_path, transport)
        runner.play_series(timeout=1.0)
        return runner, transport
    def test_the_budget_spent_is_the_one_appendix_f_documents(
        self, tmp_path: Path, stub: Install
    ) -> None:
        _, transport = self.failing_boundary(tmp_path, stub)
        spent = 1 + (BOOK_RETRIES + 1) + 1 + len(BOUNDARIES[1:])
        assert transport.tools.count("negotiate") == spent
    def test_the_boundary_is_crossed_rather_than_skipped(
        self, tmp_path: Path, stub: Install
    ) -> None:
        runner, _ = self.failing_boundary(tmp_path, stub)
        assert runner.peering is not None and runner.peering.sub_game == BOOK_SERIES
        assert [o.number for o in runner.outcomes] == list(range(1, BOOK_SERIES + 1))
    def test_the_failure_is_recorded_rather_than_swallowed_silently(
        self, tmp_path: Path, stub: Install
    ) -> None:
        runner, _ = self.failing_boundary(tmp_path, stub)
        assert "announce-failed" in runner.orchestrator.heartbeats
    def test_the_second_announcement_goes_to_the_address_we_just_adopted(
        self, tmp_path: Path, stub: Install
    ) -> None:
        _, transport = self.failing_boundary(tmp_path, stub)
        assert transport.where("negotiate")[: 2 + BOOK_RETRIES] == [AT_THEIRS] * (2 + BOOK_RETRIES)
        assert transport.where("negotiate")[2 + BOOK_RETRIES] == AT_ROTATED
    def test_the_series_still_finishes_on_the_rotated_address(
        self, tmp_path: Path, stub: Install
    ) -> None:
        runner, transport = self.failing_boundary(tmp_path, stub)
        assert transport.where("receive_turn") == [AT_THEIRS] + [AT_ROTATED] * 5
        assert runner.orchestrator.client.opponent_url == AT_ROTATED
