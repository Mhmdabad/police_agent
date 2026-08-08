from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_bluff")).items() if not k.startswith("__")})

class TestTheWordCap:
    def test_it_is_the_appendix_f_value(self) -> None:
        assert MAX_WORDS == 15
    def test_every_template_fits_once_filled(self) -> None:
        assert all(len(hint.split()) <= MAX_WORDS for hint in every_hint())
    def test_a_hint_is_never_empty(self) -> None:
        assert all(hint.strip() for hint in every_hint())
