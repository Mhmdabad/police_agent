from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_actions")).items() if not k.startswith("__")})

class TestBarrierBlocksBothPlayers:
    def test_blocks_the_thief(self) -> None:
        state = make(thief=(3, 3), barriers=frozenset({(2, 3)}))
        assert "N" not in legal_moves(state, "thief", AXES)
    def test_blocks_the_cop_that_placed_it(self) -> None:
        state = make(cop=(3, 3), barriers=frozenset({(2, 3)}))
        assert "N" not in legal_moves(state, "cop", AXES)
    def test_a_fully_walled_cop_has_only_stay(self) -> None:
        state = make(cop=(3, 3), barriers=frozenset({(2, 3), (4, 3), (3, 2), (3, 4)}))
        assert legal_moves(state, "cop", AXES) == ["STAY"]
