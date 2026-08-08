from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_match")).items() if not k.startswith("__")})

class TestOpeningASubGameDoesNotForgetWhatTheOpponentAlreadySent:
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
    def a_runner_at(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> MatchRunner:
        self.a_stub_sub_game(monkeypatch)
        runner = a_runner(tmp_path)
        runner.scent_lock = ScentAgreement(digest="a" * 64, binding="turn-message-bound")
        return runner
    @staticmethod
    def early() -> dict[str, Any]:
        return {
            "step": 1,
            "sender": "thief",
            "hint": "",
            "smell_grid": {},
            "commit": "a" * 64,
            "timestamp": WHEN,
            "game_uid": "u-0001",
            "sub_game": 2,
        }
    def test_a_turn_deferred_before_we_opened_is_taken_once_we_have(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        runner = self.a_runner_at(tmp_path, monkeypatch)
        inboxes = runner.orchestrator.inboxes
        inboxes.bind("u-0001", 1)
        assert inboxes.receive_turn(self.early())[RETRY_KEY] is True
        assert inboxes.accepted_turns == {}
        runner.play_sub_game(2)
        assert inboxes.receive_turn(self.early()) == {"ok": True}
        assert ("thief", 1, "u-0001", 2) in inboxes.accepted_turns
        assert inboxes.rejected == []
    def test_the_binding_it_advances_is_this_sub_games(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        runner = self.a_runner_at(tmp_path, monkeypatch)
        runner.play_sub_game(3)
        assert runner.orchestrator.inboxes.game_uid == "u-0001"
        assert runner.orchestrator.inboxes.sub_game == 3
