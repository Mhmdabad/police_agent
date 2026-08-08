from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_stage3")).items() if not k.startswith("__")})

class TestSelfWallOffRegression:
    def test_a_placement_that_cuts_us_off_is_refused_though_it_scores_better(
        self,
    ) -> None:
        state = make(cop=(0, 0), thief=(2, 2), barriers={(1, 0)})
        ranked = {score.at: score for score in rank_placements(state, AXES, (2, 2))}
        assert ranked[(0, 1)].disconnects
        assert ranked[(0, 1)].escape_reduction > ranked[(0, 0)].escape_reduction
        assert (0, 1) not in {score.at for score in safe_placements(state, AXES, (2, 2))}
        assert PoliceBrain(axes=AXES).decide(state, target=state.thief).action != PlaceBarrier(
            (0, 1)
        )
    def test_a_placement_leaving_no_legal_move_is_refused(self) -> None:
        state = make(cop=(0, 0), thief=(2, 2), barriers={(0, 1), (1, 0)})
        assert legal_moves(state, "cop", AXES) == ["STAY"]
        only = rank_placements(state, AXES, (2, 2))[0]
        assert only.at == (0, 0) and only.immobilises
        action = PoliceBrain(axes=AXES).decide(state, target=state.thief).action
        assert isinstance(action, MoveAction)
    def test_the_cop_never_walls_itself_in_over_a_whole_match(self) -> None:
        state = make(cop=(0, 0), thief=(6, 6))
        brain = PoliceBrain(axes=AXES)
        for step in range(35):
            if evaluate(state, AXES) is not Outcome.ONGOING:
                break
            assert legal_moves(state, "cop", AXES), f"cop immobilised at step {step}"
            state = apply_action(state, "cop", brain.decide(state, target=state.thief).action, AXES)
            state = evade(replace(state, step=step + 1))
        assert legal_moves(state, "cop", AXES)
