from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_crypto")).items() if not k.startswith("__")})

class TestCanonicalForm:
    def test_key_order_does_not_change_the_output(self) -> None:
        assert canonical({"b": 1, "a": 2}) == canonical({"a": 2, "b": 1})
    def test_no_incidental_whitespace(self) -> None:
        rendered = canonical(SAMPLE)
        assert ", " not in rendered
        assert ": " not in rendered
    def test_non_ascii_is_escaped_exactly_as_the_rulebook_does_it(self) -> None:
        ours = canonical({"hint": "רחוב"})
        book = json.dumps({"hint": "רחוב"}, sort_keys=True, separators=(",", ":"))
        assert ours == book == '{"hint":"\\u05e8\\u05d7\\u05d5\\u05d1"}'
    def test_the_output_is_pure_ascii_whatever_went_in(self) -> None:
        assert canonical({"hint": "רחוב", "note": "café", "emoji": "🚓"}).isascii()
    def test_there_is_only_one_canonical_form_in_the_codebase(self) -> None:
        payload = {"b": "רחוב", "a": 1}
        assert canonical(payload).encode("utf-8") == canonical_bytes(payload)
