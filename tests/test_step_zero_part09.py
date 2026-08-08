from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_step_zero")).items() if not k.startswith("__")})

class TestSigning:
    def test_a_key_produces_a_verifiable_signature(self, tmp_path: Path) -> None:
        declared = declaration(tmp_path)
        assert declared.signed
        assert verify_signature(declared.to_dict(), KEY)
    def test_the_wrong_key_does_not_verify(self, tmp_path: Path) -> None:
        assert not verify_signature(declaration(tmp_path).to_dict(), "someone-elses-key")
    def test_editing_any_declared_field_breaks_the_signature(self, tmp_path: Path) -> None:
        tampered = declaration(tmp_path).to_dict()
        tampered["hardware"] = {**tampered["hardware"], "logical_cores": 256}
        assert not verify_signature(tampered, KEY)
    def test_it_is_an_hmac_rather_than_a_bare_hash(self) -> None:
        content: dict[str, Any] = {"hardware": {}, "provenance": {}}
        assert sign(content, KEY) != hashlib.sha256(canonical_bytes(content)).hexdigest()
    def test_it_signs_canonical_bytes(self) -> None:
        content: dict[str, Any] = {"hardware": {"b": 1, "a": 2}, "provenance": {}}
        reordered: dict[str, Any] = {"hardware": {"a": 2, "b": 1}, "provenance": {}}
        assert sign(content, KEY) == sign(reordered, KEY)
