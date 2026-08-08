from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_stage3")).items() if not k.startswith("__")})

class TestDeterminismCriterion:
    def test_same_state_and_config_yields_the_same_action(self) -> None:
        state = make(cop=(2, 2), thief=(5, 5))
        assert (
            PoliceBrain(axes=AXES, seed=7).decide(state, target=state.thief).action
            == PoliceBrain(axes=AXES, seed=7).decide(state, target=state.thief).action
        )
    def test_a_whole_match_replays_move_for_move(self) -> None:
        def play(seed: int) -> list[object]:
            state = make(cop=(0, 0), thief=(3, 3))
            brain = PoliceBrain(axes=AXES, seed=seed)
            actions: list[object] = []
            for step in range(20):
                if evaluate(state, AXES) is not Outcome.ONGOING:
                    break
                action = brain.decide(state, target=state.thief).action
                actions.append(action)
                state = apply_action(state, "cop", action, AXES)
                state = evade(replace(state, step=step + 1))
            return actions
        assert play(1) == play(2)
        assert len(play(1)) == 20
