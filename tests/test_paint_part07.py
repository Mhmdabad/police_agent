from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_paint")).items() if not k.startswith("__")})

class TestTheWindowFits:
    @pytest.mark.parametrize("grid", [4, 8, 12])
    def test_it_grows_with_the_board(self, grid: int) -> None:
        width, height = board_size(grid)
        assert width < height, "the banner strip adds to the height"
        assert width > grid * 40
