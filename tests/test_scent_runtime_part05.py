from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_scent_runtime")).items() if not k.startswith("__")})

class TestBeliefDrivesTheNextDecision:
    def test_completed_scent_becomes_the_very_next_deterministic_context(self) -> None:
        game, _ = a_subgame(max_steps=2)
        brain = RecordingBrain(["STAY", "STAY"])
        game.brain = brain  # type: ignore[assignment]
        game.play()
        first_state, first = brain.calls[0]
        second_state, second = brain.calls[1]
        assert first == {
            "target": (0, 1),
            "concentration": 0.0,
            "uncertainty": 1.0,
        }
        assert game.received_hints[1] == "t1"
        assert game.belief.at(OUR_START) == 0.0
        assert first["target"] != THEIR_START
        assert second["target"] == THEIR_START
        assert second["concentration"] > 0.0  # type: ignore[operator]
        assert second["uncertainty"] == pytest.approx(1.0 - second["concentration"])  # type: ignore[operator]
        assert first_state.thief == first["target"]
        assert second_state.thief == second["target"]
    def test_old_explicit_strategy_signature_remains_supported(self) -> None:
        class ExplicitBrain(RecordingBrain):
            def decide(  # type: ignore[override]
                self,
                state: BoardState,
                *,
                target: tuple[int, int],
                concentration: float,
                uncertainty: float,
            ) -> Decision:
                return super().decide(
                    state,
                    target=target,
                    concentration=concentration,
                    uncertainty=uncertainty,
                )
        game, _ = a_subgame(max_steps=2)
        game.brain = ExplicitBrain(["STAY", "STAY"])  # type: ignore[assignment]
        game.play()
    def test_malformed_scent_and_our_own_scent_cannot_poison_context(self) -> None:
        game, _ = a_subgame(ScentedOpponent(junk=True), moves=["STAY", "STAY"], max_steps=2)
        brain = RecordingBrain(["STAY", "STAY"])
        game.brain = brain  # type: ignore[assignment]
        game.play()
        assert [call[1]["target"] for call in brain.calls] == [(0, 1), (0, 1)]
        assert all(call[1]["concentration"] == 0.0 for call in brain.calls)
    def test_physically_forged_step_one_cannot_redirect_step_two(self) -> None:
        game, _ = a_subgame(ScentedOpponent(forge_at=1), max_steps=2)
        brain = RecordingBrain(["STAY", "STAY"])
        game.brain = brain  # type: ignore[assignment]
        played = game.play()
        assert brain.calls[1][1]["target"] == (0, 1)
        assert not played.audit.clean
        assert any("step 1" in failure for failure in played.audit.failures)
    def test_barriers_and_zero_mass_are_never_selected(self) -> None:
        game, _ = a_subgame(max_steps=1)
        brain = RecordingBrain(["STAY"])
        game.brain = brain  # type: ignore[assignment]
        game.state = replace(game.state, barriers=frozenset({(0, 1)}))
        game.belief.mass = {(0, 1): 9.0, (1, 1): 0.0, (1, 0): 1.0}
        game.play()
        assert brain.calls[0][1]["target"] == (1, 0)
    def test_context_is_not_added_to_gui_or_log(self) -> None:
        game, _ = a_subgame(max_steps=1)
        brain = RecordingBrain(["STAY"])
        game.brain = brain  # type: ignore[assignment]
        game.play()
        reveal = game.log.entries[1].reveal
        assert reveal is not None
        assert not ({"target", "concentration", "uncertainty"} & reveal.keys())
    def test_incompatible_configured_brain_gets_a_migration_error(self) -> None:
        class LegacyBrain:
            def decide(self, state: BoardState) -> Decision:
                return Decision(MoveAction("STAY"))
        game, _ = a_subgame(max_steps=1)
        game.brain = LegacyBrain()  # type: ignore[assignment]
        with pytest.raises(StrategyContextError, match=r"accept \*\*context.*target"):
            game.play()
    def test_shipped_police_pursues_belief_not_the_true_coordinate(self) -> None:
        game, _ = a_subgame(max_steps=1)
        game.state = replace(game.state, cop=(3, 3), thief=(0, 0))
        game.brain = PoliceBrain(axes=AXES, max_barriers=0)
        game.belief.mass = {(6, 3): 1.0}
        game.play()
        opened = game.ceremony.at(1).revealed_ours
        assert opened is not None and opened.move == "S"
    def test_shipped_police_decision_changes_when_only_belief_changes(self) -> None:
        moves: list[str] = []
        for peak in ((0, 3), (6, 3)):
            game, _ = a_subgame(max_steps=1)
            game.state = replace(game.state, cop=(3, 3), thief=(3, 6))
            game.brain = PoliceBrain(axes=AXES, max_barriers=0)
            game.belief.mass = {peak: 1.0}
            game.play()
            opened = game.ceremony.at(1).revealed_ours
            assert opened is not None
            moves.append(opened.move)
        assert moves == ["N", "S"]
