from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_bluff")).items() if not k.startswith("__")})

class TestNoCoordinates:
    def test_nothing_we_emit_could_be_a_coordinate_protocol(self) -> None:
        assert not any(NUMERIC.search(hint) for hint in every_hint())
    def test_no_digits_at_all(self) -> None:
        assert not any(char.isdigit() for hint in every_hint() for char in hint)
    def test_our_own_parser_reads_what_we_write(self) -> None:
        for hint in every_hint():
            assert parse(hint, BOARD, (3, 3)), hint
