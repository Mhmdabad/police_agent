from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_paint")).items() if not k.startswith("__")})

class TestTheReplayStamp:
    def test_a_clean_log_stamps_green(self, tmp_path: Path) -> None:
        painter = Recording()
        summary = draw_replay(load(sealed_log(tmp_path)), painter)  # type: ignore[arg-type]
        assert painter.rects[0].fill == STAMP_COLOUR[Stamp.VERIFIED_OK]
        assert "Verified OK" in summary
    def test_a_tampered_log_stamps_blazing_red(self, tmp_path: Path) -> None:
        painter = Recording()
        summary = draw_replay(load(sealed_log(tmp_path, corrupt=True)), painter)  # type: ignore[arg-type]
        assert painter.rects[0].fill == STAMP_COLOUR[Stamp.TAMPERED]
        assert "TAMPERED" in summary
    def test_the_verdict_covers_the_whole_log_not_the_step_on_screen(self, tmp_path: Path) -> None:
        replay = load(sealed_log(tmp_path, corrupt=True))
        assert replay.current.step == 1, "the reader is on an honest step"
        painter = Recording()
        draw_replay(replay, painter)  # type: ignore[arg-type]
        assert painter.rects[0].fill == STAMP_COLOUR[Stamp.TAMPERED]
    def test_the_stamp_says_the_words_the_rulebook_uses(self, tmp_path: Path) -> None:
        painter = Recording()
        draw_replay(load(sealed_log(tmp_path)), painter)  # type: ignore[arg-type]
        assert painter.texts[0].body == "Verified OK"
