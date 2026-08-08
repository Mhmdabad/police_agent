from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_paint")).items() if not k.startswith("__")})

class TestDeeperRedMeansHigherProbability:
    def test_the_peak_is_the_hottest_band(self) -> None:
        painter = Recording()
        view = a_view()
        paint_board(view, painter)
        assert view.suspected is not None
        assert painter.fill_at(view.suspected) == HEAT[-1]
    def test_our_own_marker_is_never_the_suspect_colour(self) -> None:
        state = BoardState(grid_size=6, cop=(0, 0), thief=(4, 4), barriers=frozenset(), step=1)
        painter = Recording()
        view = a_view(state)
        paint_board(view, painter)
        assert view.suspected == (0, 0), "the belief should peak on our own cell here"
        assert [t.fill for t in painter.texts if t.body == "C"] == [OURS]
    def test_the_suspected_cell_is_marked_and_coloured_apart(self) -> None:
        painter = Recording()
        view = a_view()
        paint_board(view, painter)
        assert view.suspected is not None
        marked = [t for t in painter.texts if t.fill == SUSPECT]
        assert len(marked) == 1
        assert marked[0].body == "T?", "the mark is a guess about the thief, not a bare ?"
    def test_our_marker_is_not_the_suspect_colour(self) -> None:
        painter = Recording()
        paint_board(a_view(), painter)
        ours = [t for t in painter.texts if t.body == "C"]
        assert ours and ours[0].fill == OURS
    def test_the_bands_run_dark_to_red(self) -> None:
        assert len(HEAT) == 5
        assert HEAT[0] != HEAT[-1]
