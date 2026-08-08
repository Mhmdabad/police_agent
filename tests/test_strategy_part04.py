from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_strategy")).items() if not k.startswith("__")})

class TestDeterminism:
    def test_same_state_and_seed_yields_the_same_action(self) -> None:
        state = make(cop=(2, 2), thief=(5, 5))
        first = PoliceBrain(axes=AXES, seed=7).decide(state).action
        second = PoliceBrain(axes=AXES, seed=7).decide(state).action
        assert first == second
    def test_the_seed_is_recorded_on_the_brain(self) -> None:
        assert PoliceBrain(axes=AXES, seed=99).seed == 99
    def test_randomness_is_seeded_not_global(self) -> None:
        a = PoliceBrain(axes=AXES, seed=1).rng.random()
        b = PoliceBrain(axes=AXES, seed=1).rng.random()
        assert a == b
    def test_different_seeds_give_different_streams(self) -> None:
        a = PoliceBrain(axes=AXES, seed=1).rng.random()
        b = PoliceBrain(axes=AXES, seed=2).rng.random()
        assert a != b
