from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_match")).items() if not k.startswith("__")})

class TestLockingTheScentModelComesNext:
    def test_a_matching_lock_is_recorded_on_the_runner(self, tmp_path: Path) -> None:
        runner = answered(a_runner(tmp_path))
        runner.agree()
        assert runner.scent_lock == propose().agreement()
    def test_the_offer_is_bound_to_this_runners_series(self, tmp_path: Path) -> None:
        transport = Answering({"ok": True})
        runner = answered(a_runner(tmp_path, transport=transport))
        runner.agree()
        assert transport.calls[1][1]["message"]["game_uid"] == runner.declaration.game_uid
    def test_a_peer_on_another_falloff_aborts_the_series(self, tmp_path: Path) -> None:
        runner = answered(a_runner(tmp_path), lock=propose(CHEBYSHEV))
        with pytest.raises(MatchAborted) as excinfo:
            runner.agree()
        assert excinfo.value.cause is TechnicalLoss.ILLEGAL_ACTION
        assert runner.scent_lock is None and runner.outcomes == []
    def test_a_peer_that_locks_nothing_times_out(self, tmp_path: Path) -> None:
        runner = a_runner(tmp_path)
        runner.orchestrator.inboxes.negotiate(
            {"config_sha256": config_sha256(runner.parameters), "game_uid": "u-0001"}
        )
        with pytest.raises(MatchAborted) as excinfo:
            runner.agree(timeout=0.0)
        assert excinfo.value.cause is TechnicalLoss.TIMEOUT
        assert runner.scent_lock is None
    def test_a_config_refusal_stops_before_any_lock_is_offered(self, tmp_path: Path) -> None:
        transport = Answering({"ok": False, "detail": "digest mismatch"})
        runner = a_runner(tmp_path, transport=transport)
        with pytest.raises(MatchAborted):
            runner.agree()
        assert [call[1]["message"].get("scent_lock") for call in transport.calls] == [None]
    def test_no_sub_game_opens_without_one(self, tmp_path: Path) -> None:
        runner = a_runner(tmp_path)
        with pytest.raises(MatchAborted) as excinfo:
            runner.play_sub_game(1)
        assert excinfo.value.cause is TechnicalLoss.ILLEGAL_ACTION
        assert runner.outcomes == []
