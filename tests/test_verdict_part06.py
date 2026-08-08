from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_verdict")).items() if not k.startswith("__")})

class TestAttestationOnItsOwn:
    def test_a_clean_attestation_is_clean_and_not_void(self) -> None:
        result = Attestation(Stamp.VERIFIED_OK, verified=9, total=9)
        assert result.clean and not result.void
    def test_only_tampered_voids(self) -> None:
        assert not Attestation(Stamp.INCOMPLETE, 0, 3, at_step=1, reason="x").void
