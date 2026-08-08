from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_declaration")).items() if not k.startswith("__")})

class TestTheSignature:
    def test_it_verifies_against_the_key(self) -> None:
        assert verify_signature(declared().to_dict(), KEY) is False, (
            "step_zero verifies its own two-field statement, not this document"
        )
    def test_a_signed_declaration_is_not_marked_unsigned(self) -> None:
        assert declared().signature != UNSIGNED
    def test_no_key_produces_an_explicit_unsigned(self) -> None:
        assert declared(key=None).signature == UNSIGNED
    def test_the_signature_covers_the_content_and_not_itself(self) -> None:
        assert "signature" not in declared().content()
    def test_re_signing_the_same_content_is_stable(self) -> None:
        assert declare_match(declared(), KEY).signature == declared().signature
    def test_changing_any_field_changes_the_signature(self) -> None:
        assert declared().signature != declared(token_ceiling=100_000).signature
    def test_changing_an_opponent_link_changes_the_signature(self) -> None:
        other = Team(name="uoh26-others", members=("A Person",), cop_repo="x", thief_repo="y")
        assert declared().signature != declared(them=other).signature
    def test_a_different_key_produces_a_different_signature(self) -> None:
        assert declared().signature != declared(key="another-key").signature
