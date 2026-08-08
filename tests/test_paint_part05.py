from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_paint")).items() if not k.startswith("__")})

class TestTheLiveWindowIsNeverGivenTheirCell:
    def test_drawing_a_frame_uses_only_our_position(self) -> None:
        canvas = TestTheCanvasAdapter.FakeCanvas()
        state = a_board()
        draw_live(state, Belief.uniform(state), "police", state.cop, CanvasPainter(canvas))
        assert canvas.calls, "nothing was drawn"
    def test_the_thiefs_true_cell_is_not_drawn_as_a_certainty(self) -> None:
        painter = Recording()
        paint_board(a_view(), painter)
        glyphs = [t.body for t in painter.texts]
        assert "T" not in glyphs, "the opponent's real marker was drawn as a certainty"
        assert "T?" in glyphs, "the belief's peak should be marked as a guess"
