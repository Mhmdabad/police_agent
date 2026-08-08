from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_crypto")).items() if not k.startswith("__")})

class TestCommitFormula:
    def test_it_matches_the_rulebooks_own_commit(self) -> None:
        secret = "abc123"
        book = hashlib.sha256(
            json.dumps({**SAMPLE, "nonce": secret}, sort_keys=True, separators=(",", ":")).encode(
                "utf-8"
            )
        ).hexdigest()
        assert commit_of(SAMPLE, secret) == book
    def test_appending_the_nonce_would_give_a_different_digest(self) -> None:
        secret = "abc123"
        appended = hashlib.sha256(f"{canonical(SAMPLE)}|{secret}".encode()).hexdigest()
        assert commit_of(SAMPLE, secret) != appended
    def test_a_payload_carrying_its_own_nonce_is_refused(self) -> None:
        with pytest.raises(CryptoError, match="pass it once"):
            commit_of({**SAMPLE, "nonce": "already"}, "abc123")
    def test_is_stable_across_calls(self) -> None:
        assert commit_of(SAMPLE, "n") == commit_of(SAMPLE, "n")
    def test_key_order_does_not_change_the_commit(self) -> None:
        reordered = dict(reversed(list(SAMPLE.items())))
        assert commit_of(SAMPLE, "n") == commit_of(reordered, "n")
    def test_any_payload_change_changes_the_commit(self) -> None:
        assert commit_of(SAMPLE, "n") != commit_of({**SAMPLE, "move": "S"}, "n")
    def test_any_nonce_change_changes_the_commit(self) -> None:
        assert commit_of(SAMPLE, "n1") != commit_of(SAMPLE, "n2")
    def test_a_known_fixture_pins_the_digest(self) -> None:
        digest = commit_of({"move": "N", "step": 1}, "0" * 32)
        expected = hashlib.sha256(b'{"move":"N","nonce":"' + b"0" * 32 + b'","step":1}').hexdigest()
        assert digest == expected
        assert len(digest) == 64
