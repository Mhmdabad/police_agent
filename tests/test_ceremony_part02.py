from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_ceremony")).items() if not k.startswith("__")})

class TestWhatItRefuses:
    @pytest.mark.parametrize("sender", ["cop", "referee", "POLICE", ""])
    def test_a_role_the_wire_does_not_name(self, sender: str) -> None:
        with pytest.raises(CeremonyError, match="sender must be one of"):
            commitment(sender=sender)
    def test_a_negative_step(self) -> None:
        with pytest.raises(CeremonyError, match="step must be >= 0"):
            commitment(step=-1)
    @pytest.mark.parametrize(
        "digest",
        ["a" * 63, "a" * 65, "A" * 64, "g" * 64, "", "0x" + "a" * 62, "a" * 32],
    )
    def test_a_digest_that_is_not_a_sha256_hexdigest(self, digest: str) -> None:
        with pytest.raises(CeremonyError, match="64 lowercase hex"):
            commitment(commit=digest)
    def test_it_is_frozen_because_an_editable_commitment_is_not_one(self) -> None:
        with pytest.raises(AttributeError):
            commitment().commit = "b" * 64  # type: ignore[misc]
