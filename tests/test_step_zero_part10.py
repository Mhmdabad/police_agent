from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_step_zero")).items() if not k.startswith("__")})

class TestWithoutTheKey:
    def test_no_key_declares_itself_unsigned(self, tmp_path: Path) -> None:
        declared = declaration(tmp_path, key=None)
        assert not declared.signed
        assert declared.to_dict()["signature"] == UNSIGNED
    def test_an_unsigned_declaration_never_verifies(self, tmp_path: Path) -> None:
        assert not verify_signature(declaration(tmp_path, key=None).to_dict(), KEY)
    @pytest.mark.parametrize("claimed", [None, 42, "", UNSIGNED])
    def test_a_missing_or_unsigned_claim_is_refused(self, claimed: object) -> None:
        assert not verify_signature({"hardware": {}, "provenance": {}, "signature": claimed}, KEY)
