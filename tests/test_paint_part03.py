from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_paint")).items() if not k.startswith("__")})

class TestTheBanner:
    def test_a_live_turn_is_drawn_in_its_tone(self) -> None:
        painter = Recording()
        paint_banner(banner(StepCeremony(step=1, role="police")), 6, painter)
        assert painter.rects[0].fill == Tone.GO.value
    def test_the_banner_spans_the_window(self) -> None:
        painter = Recording()
        paint_banner(banner(StepCeremony(step=1, role="police")), 6, painter)
        assert painter.rects[0].x1 == board_size(6)[0]
    def test_the_text_is_drawn(self) -> None:
        painter = Recording()
        paint_banner(banner(StepCeremony(step=1, role="police")), 6, painter)
        assert "YOUR TURN" in painter.texts[0].body
