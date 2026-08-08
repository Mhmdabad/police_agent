from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_paint")).items() if not k.startswith("__")})

class TestTheBoardIsDrawn:
    def test_every_square_gets_a_rectangle(self) -> None:
        painter = Recording()
        paint_board(a_view(), painter)
        assert len(painter.rects) == 36
    def test_our_position_carries_our_glyph(self) -> None:
        painter = Recording()
        paint_board(a_view(), painter)
        assert painter.glyph_at((3, 3)) == "C"
    def test_a_barrier_cell_is_darker_than_the_coldest_belief(self) -> None:
        painter = Recording()
        paint_board(a_view(), painter)
        assert painter.fill_at((2, 2)) == BARRIER_FILL
        assert HEAT[0] != BARRIER_FILL
    def test_a_barrier_carries_no_glyph(self) -> None:
        painter = Recording()
        paint_board(a_view(), painter)
        assert painter.glyph_at((2, 2)) == ""
    def test_rows_map_to_y_and_columns_to_x(self) -> None:
        first, second = cell_box((0, 1)), cell_box((1, 0))
        assert first[0] > second[0], "column should move x"
        assert second[1] > first[1], "row should move y"
