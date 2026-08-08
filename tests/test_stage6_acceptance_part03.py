from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_stage6_acceptance")).items() if not k.startswith("__")})

class TestNoNonceLeavesEarly:
    def test_no_nonce_appears_before_the_final_reveal(self) -> None:
        game = play()
        secrets = {c.our_nonce for c in game.cop.match.steps.values() if c.our_nonce}
        secrets |= {c.our_nonce for c in game.thief.match.steps.values() if c.our_nonce}
        assert len(secrets) == STEPS * 2
        early = "\n".join(body for kind, body in game.wire.sent if kind != "final_reveal")
        for secret in secrets:
            assert secret not in early
    def test_every_nonce_appears_in_the_final_reveal(self) -> None:
        game = play()
        late = "\n".join(body for kind, body in game.wire.sent if kind == "final_reveal")
        for ceremony in (*game.cop.match.steps.values(), *game.thief.match.steps.values()):
            assert ceremony.our_nonce and ceremony.our_nonce in late
    def test_the_word_nonce_never_appears_in_a_commit_or_reveal(self) -> None:
        for kind, body in play().wire.sent:
            if kind in ("commit", "reveal", "ack"):
                assert "nonce" not in body
    def test_reveals_are_only_sent_once_both_sides_are_locked(self) -> None:
        kinds = [kind for kind, _ in play().wire.sent]
        for step in range(STEPS):
            window = kinds[step * 6 : step * 6 + 6]
            assert window == ["commit", "commit", "ack", "ack", "reveal", "reveal"]
