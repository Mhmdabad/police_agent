from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_scent_lock_negotiation")).items() if not k.startswith("__")})

class TestTheExistingGatesSurvive:
    def test_agree_still_returns_the_config_digest(
        self, wire: tuple[Side, Side], tmp_path: Path
    ) -> None:
        ours, theirs = fresh(wire)
        runner = a_runner(ours, parameters(), tmp_path)
        done = concurrently(
            {
                "ours": lambda: runner.agree(timeout=PATIENCE),
                "theirs": lambda: TestTheAgreementReachesEverySubGame.peer_negotiation(theirs),
            }
        )
        assert done["ours"] == config_sha256(parameters())
        assert theirs.inboxes.digests.empty() and theirs.inboxes.scent_locks.empty()
    def test_a_config_mismatch_aborts_before_any_lock_is_offered(
        self, wire: tuple[Side, Side], tmp_path: Path
    ) -> None:
        ours, theirs = fresh(wire)
        runner = a_runner(ours, altered(), tmp_path)
        done = concurrently(
            {
                "ours": lambda: runner.agree(timeout=PATIENCE),
                "theirs": lambda: theirs.orchestrator.agree_config(
                    parameters(), game_uid=GAME_UID, timeout=PATIENCE
                ),
            }
        )
        assert isinstance(done["ours"], MatchAborted)
        assert theirs.inboxes.scent_locks.empty()
        assert runner.scent_lock is None
    def test_a_series_is_still_six_sub_games(self, wire: tuple[Side, Side], tmp_path: Path) -> None:
        ours, _ = fresh(wire)
        assert a_runner(ours, parameters(), tmp_path).sub_games == 6
