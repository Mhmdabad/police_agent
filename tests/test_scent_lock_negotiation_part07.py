from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_scent_lock_negotiation")).items() if not k.startswith("__")})

class TestTheAgreementReachesEverySubGame:
    @staticmethod
    def a_stub_sub_game(monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            SubGame,
            "play",
            lambda self: Played(
                steps=0,
                final=self.state,
                captured=False,
                reason="stubbed",
                audit=AuditResult(verdict=Verdict.CLEAN, checked=0),
            ),
        )
        monkeypatch.setattr(
            SubGame, "audit", lambda self: AuditResult(verdict=Verdict.CLEAN, checked=0)
        )
    def test_a_runner_starts_with_no_agreement(
        self, wire: tuple[Side, Side], tmp_path: Path
    ) -> None:
        ours, _ = fresh(wire)
        assert a_runner(ours, parameters(), tmp_path).scent_lock is None
    def test_a_runner_without_one_plays_nothing(
        self, wire: tuple[Side, Side], tmp_path: Path
    ) -> None:
        ours, _ = fresh(wire)
        runner = a_runner(ours, parameters(), tmp_path)
        with pytest.raises(MatchAborted) as excinfo:
            runner.play_sub_game(1, timeout=BRIEF)
        assert excinfo.value.cause is TechnicalLoss.ILLEGAL_ACTION
        assert runner.outcomes == []
    def test_agreeing_records_the_lock_on_the_runner(
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
        assert not isinstance(done["ours"], BaseException), done
        assert runner.scent_lock == our_lock()
    @staticmethod
    def peer_negotiation(side: Side) -> str:
        side.orchestrator.agree_config(parameters(), game_uid=GAME_UID, timeout=PATIENCE)
        side.orchestrator.agree_scent_model(game_uid=GAME_UID, timeout=PATIENCE)
        return "done"
    def test_the_sub_game_requires_bound_scent_from_the_agreement(
        self, wire: tuple[Side, Side], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        ours, _ = fresh(wire)
        self.a_stub_sub_game(monkeypatch)
        runner = a_runner(ours, parameters(), tmp_path)
        runner.scent_lock = our_lock()
        game = runner.play_sub_game(1, timeout=BRIEF).game
        assert game is not None and game.require_bound_scent is True
    def test_it_is_derived_rather_than_hard_coded(
        self, wire: tuple[Side, Side], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        ours, _ = fresh(wire)
        self.a_stub_sub_game(monkeypatch)
        runner = a_runner(ours, parameters(), tmp_path)
        runner.scent_lock = ScentAgreement(digest="a" * 64, binding="turn-message-unbound")
        game = runner.play_sub_game(1, timeout=BRIEF).game
        assert game is not None and game.require_bound_scent is False
    def test_the_agreed_binding_is_the_commit_bound_one(self) -> None:
        assert our_lock().binding == BINDING
        assert our_lock().require_bound_scent is True
    def test_every_sub_game_of_the_series_gets_it(
        self, wire: tuple[Side, Side], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        ours, _ = fresh(wire)
        self.a_stub_sub_game(monkeypatch)
        stub_boundaries(monkeypatch)
        runner = a_runner(ours, parameters(), tmp_path)
        runner.scent_lock = our_lock()
        outcomes = runner.play_series(timeout=BRIEF)
        assert [outcome.number for outcome in outcomes] == [1, 2, 3, 4, 5, 6]
        assert all(o.game is not None and o.game.require_bound_scent for o in outcomes)
