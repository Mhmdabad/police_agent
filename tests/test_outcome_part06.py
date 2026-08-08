from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_outcome")).items() if not k.startswith("__")})

class TestOnlyTheBoardCanProduceAClaim:
    def test_an_ordinary_position_yields_nothing(self) -> None:
        assert capture_claim(board(), AXES) is None
    def test_standing_on_the_thief_yields_a_claim_naming_the_cell(self) -> None:
        assert capture_claim(board(cop=(3, 3)), AXES) == (3, 3)
    def test_sealing_the_thief_in_place_yields_a_claim(self) -> None:
        assert capture_claim(board(barriers=frozenset({(3, 3)})), AXES) == (3, 3)
    def test_walling_the_thief_in_yields_a_claim(self) -> None:
        walled = board(cop=(5, 5), thief=(0, 0), barriers=frozenset({(0, 1), (1, 0)}))
        assert capture_claim(walled, AXES) == (0, 0)
    def test_it_takes_the_board_and_nothing_else(self) -> None:
        assert set(inspect.signature(capture_claim).parameters) == {"state", "axes"}
    def test_it_is_the_only_emitter_in_the_package(self) -> None:
        offenders = [
            path.relative_to(SRC)
            for path in sorted(SRC.rglob("*.py"))
            if path.name != "outcome.py" and re.search(r'"capture_claim"\s*:', path.read_text())
        ]
        assert offenders == []
