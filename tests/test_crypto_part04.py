from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_crypto")).items() if not k.startswith("__")})

class TestSeal:
    def test_returns_a_nonce_and_a_commit(self) -> None:
        sealed = seal(SAMPLE)
        assert set(sealed) == {"nonce", "commit"}
    def test_the_nonce_is_the_agreed_length(self) -> None:
        assert len(seal(SAMPLE)["nonce"]) == NONCE_BYTES * 2
    def test_nonces_are_fresh_each_time(self) -> None:
        assert seal(SAMPLE)["commit"] != seal(SAMPLE)["commit"]
    def test_the_sealed_commit_verifies(self) -> None:
        sealed = seal(SAMPLE)
        verify(SAMPLE, sealed["nonce"], sealed["commit"])
