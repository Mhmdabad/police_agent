from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_match")).items() if not k.startswith("__")})

class TestAgreeingTheConfigComesFirst:
    def test_a_matching_digest_lets_the_match_start(self, tmp_path: Path) -> None:
        assert len(answered(a_runner(tmp_path)).agree()) == 64
    def test_the_digest_is_of_the_parameters_we_are_actually_playing(self, tmp_path: Path) -> None:
        runner = answered(a_runner(tmp_path))
        assert runner.agree() == config_sha256(runner.parameters)
    def test_a_refusal_aborts_before_a_single_move(self, tmp_path: Path) -> None:
        runner = a_runner(tmp_path, reply={"ok": False, "detail": "digest mismatch"})
        with pytest.raises(MatchAborted):
            runner.agree()
    def test_nothing_was_played_when_it_refuses(self, tmp_path: Path) -> None:
        runner = a_runner(tmp_path, reply={"ok": False, "detail": "no"})
        with pytest.raises(MatchAborted):
            runner.agree()
        assert runner.outcomes == []
    def test_an_opponent_on_other_parameters_aborts_the_series(self, tmp_path: Path) -> None:
        runner = answered(a_runner(tmp_path), digest="b" * 64)
        with pytest.raises(MatchAborted) as excinfo:
            runner.agree()
        assert excinfo.value.cause is TechnicalLoss.ILLEGAL_ACTION
        assert runner.outcomes == []
    def test_an_opponent_that_never_negotiates_times_out(self, tmp_path: Path) -> None:
        runner = a_runner(tmp_path)
        with pytest.raises(MatchAborted) as excinfo:
            runner.agree(timeout=0.0)
        assert excinfo.value.cause is TechnicalLoss.TIMEOUT
        assert runner.outcomes == []
    def test_the_digest_is_bound_to_this_runners_series(self, tmp_path: Path) -> None:
        transport = Answering({"ok": True})
        runner = answered(a_runner(tmp_path, transport=transport))
        runner.agree()
        assert transport.calls[0][1]["message"]["game_uid"] == runner.declaration.game_uid
    def test_a_digest_agreed_for_another_series_does_not_open_this_one(
        self, tmp_path: Path
    ) -> None:
        runner = a_runner(tmp_path)
        runner.orchestrator.inboxes.negotiate(
            {"config_sha256": config_sha256(runner.parameters), "game_uid": "u-9999"}
        )
        with pytest.raises(MatchAborted) as excinfo:
            runner.agree(timeout=0.0)
        assert excinfo.value.cause is TechnicalLoss.TIMEOUT
