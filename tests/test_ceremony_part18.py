from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_ceremony")).items() if not k.startswith("__")})

class TestVerifyStep:
    def test_an_honest_record_verifies(self) -> None:
        record = step_record(sealed_state(1), "thief", "S", "truth", "hint")
        assert verify_step(record, THEIR_NONCE, commit_of(record, THEIR_NONCE))
    def test_a_changed_record_does_not(self) -> None:
        record = step_record(sealed_state(1), "thief", "S", "truth", "hint")
        commit = commit_of(record, THEIR_NONCE)
        changed = step_record(sealed_state(1), "thief", "N", "truth", "hint")
        assert not verify_step(changed, THEIR_NONCE, commit)
    def test_it_uses_a_constant_time_comparison(self) -> None:
        source = (SRC / "infra" / "ceremony.py").read_text()
        assert "secrets.compare_digest(" in source
