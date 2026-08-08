from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_tradeoff")).items() if not k.startswith("__")})

class TestOpenBoardRefusesByDefault:
    def test_a_barrier_on_open_ground_never_beats_the_step(self) -> None:
        for cop in ((0, 0), (1, 1), (2, 2), (3, 4), (5, 1)):
            state = board(cop=cop, thief=(3, 3))
            move = PoliceBrain(axes=AXES)._pick_move(state, target=state.thief)
            assert not weigh(state, AXES, (3, 3), move).place
    def test_so_the_cop_moves(self) -> None:
        state = board(cop=(0, 0), thief=(3, 3))
        action = PoliceBrain(axes=AXES).decide(state, target=state.thief).action
        assert isinstance(action, MoveAction)
