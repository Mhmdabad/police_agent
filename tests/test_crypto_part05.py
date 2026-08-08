from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_crypto")).items() if not k.startswith("__")})

class TestVerify:
    def test_an_honest_reveal_passes(self) -> None:
        verify(SAMPLE, "n", commit_of(SAMPLE, "n"))
    def test_a_changed_move_is_caught(self) -> None:
        with pytest.raises(CryptoError, match="commit mismatch"):
            verify({**SAMPLE, "move": "S"}, "n", commit_of(SAMPLE, "n"))
    def test_a_changed_hint_is_caught(self) -> None:
        with pytest.raises(CryptoError):
            verify({**SAMPLE, "hint": "downtown"}, "n", commit_of(SAMPLE, "n"))
    def test_a_wrong_nonce_is_caught(self) -> None:
        with pytest.raises(CryptoError):
            verify(SAMPLE, "wrong", commit_of(SAMPLE, "n"))
    def test_the_error_shows_both_digests_truncated(self) -> None:
        with pytest.raises(CryptoError, match="declared .*recomputed"):
            verify(SAMPLE, "wrong", commit_of(SAMPLE, "n"))
