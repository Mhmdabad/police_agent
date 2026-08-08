from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_localhost_match")).items() if not k.startswith("__")})

class TestAWholeMatchRunsThroughTheRunner:
    @staticmethod
    def runner_for(side: Side, where: Path) -> MatchRunner:
        return MatchRunner(
            orchestrator=Orchestrator(inboxes=side.inboxes, client=side.client, role=side.role),
            declaration=build_declaration(side.role, "uoh26-s82kma9e", "u-0001"),
            parameters=parameters(),
            brain=PlaysItsOwnPiece("cop" if side.role == "police" else "thief"),  # type: ignore[arg-type]
            axes=AXES,
            start=BoardState(grid_size=8, cop=(0, 0), thief=(6, 5), barriers=frozenset(), step=0),
            max_steps=STEPS,
            directory=where,
            now=lambda: WHEN,
        )
    def outcome_from(self, side: Side) -> SubGameOutcome:
        result = played_game(side).play_result
        assert result is not None, "the fixture should have played the sub-game"
        return SubGameOutcome(
            number=1, played=result, audit=played_game(side).audit(), log=played_log(side)
        )
    def test_the_played_sub_game_audits_clean(self, played: tuple[Side, Side, Path]) -> None:
        cop, _, where = played
        runner = self.runner_for(cop, where / "runner")
        runner.outcomes.append(self.outcome_from(cop))
        assert runner.opponent_played_fairly
        assert runner.failures() == []
    def test_it_writes_a_coherent_set_of_artefacts(self, played: tuple[Side, Side, Path]) -> None:
        cop, _, where = played
        runner = self.runner_for(cop, where / "runner-write")
        runner.outcomes.append(self.outcome_from(cop))
        written = runner.write(result_for(cop, "uoh26-s82kma9e", "u-0001"))
        assert {path.name for path in written} == {
            "declaration_uoh26-s82kma9e.json",
            "config_uoh26-s82kma9e_g01.json",
            "log_uoh26-s82kma9e_g01.json",
            "result_uoh26-s82kma9e.json",
        }
    def test_the_config_it_locks_carries_the_agreed_digest(
        self, played: tuple[Side, Side, Path]
    ) -> None:
        cop, thief, where = played
        ours = self.runner_for(cop, where / "a").config_for(1)
        theirs = self.runner_for(thief, where / "b").config_for(1)
        assert ours.agrees_with(theirs.sha256)
    def test_the_log_in_the_set_still_stamps_verified_ok(
        self, played: tuple[Side, Side, Path]
    ) -> None:
        cop, _, where = played
        runner = self.runner_for(cop, where / "runner-stamp")
        runner.outcomes.append(self.outcome_from(cop))
        written = runner.write(result_for(cop, "uoh26-s82kma9e", "u-0001"))
        log = next(path for path in written if path.name.startswith("log_"))
        assert walk(load(log)).stamp is Stamp.VERIFIED_OK
    def test_nothing_in_the_runner_sends_mail(self) -> None:
        source = (
            Path(__file__).resolve().parent.parent / "src/cop_agent/runtime/match.py"
        ).read_text()
        assert "Mailer" not in source
        assert "send_report" not in source
