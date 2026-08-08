from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_paint")).items() if not k.startswith("__")})

class TestTheCanvasAdapter:
    class FakeCanvas:
        def __init__(self) -> None:
            self.calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []
        def create_rectangle(self, *coords: object, **options: object) -> object:
            self.calls.append(("rect", coords, options))
            return None
        def create_text(self, *coords: object, **options: object) -> object:
            self.calls.append(("text", coords, options))
            return None
        def delete(self, tag: str) -> object:
            self.calls.append(("delete", (tag,), {}))
            return None
    def test_a_rectangle_reaches_the_canvas(self) -> None:
        canvas = self.FakeCanvas()
        CanvasPainter(canvas).rectangle(1, 2, 3, 4, "#fff", "#000")
        kind, coords, options = canvas.calls[0]
        assert kind == "rect"
        assert coords == (1, 2, 3, 4)
        assert options["fill"] == "#fff"
    def test_text_reaches_the_canvas(self) -> None:
        canvas = self.FakeCanvas()
        CanvasPainter(canvas).text(5, 6, "C", "#fff")
        kind, coords, options = canvas.calls[0]
        assert kind == "text"
        assert options["text"] == "C"
    def test_clear_wipes_everything(self) -> None:
        canvas = self.FakeCanvas()
        CanvasPainter(canvas).clear()
        assert canvas.calls[0] == ("delete", ("all",), {})
