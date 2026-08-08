from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_scent_runtime")).items() if not k.startswith("__")})

class TestTheAuditJudgesTheField:
    def test_an_honest_opponent_audits_clean(self) -> None:
        game, _ = a_subgame()
        played = game.play()
        assert played.audit.clean, str(played.audit)
    def test_a_forged_field_fails_the_audit(self) -> None:
        game, _ = a_subgame(ScentedOpponent(forge_at=2))
        played = game.play()
        assert not played.audit.clean
        assert any("step 2" in failure for failure in played.audit.failures)
    def test_a_malformed_field_fails_the_audit_without_crashing(self) -> None:
        game, _ = a_subgame(ScentedOpponent(junk=True))
        played = game.play()
        assert not played.audit.clean
    def test_a_peer_that_cannot_bind_scent_is_refused(self) -> None:
        game, _ = a_subgame(ScentedOpponent(omit=True))
        played = game.play()
        assert not played.audit.clean
        assert any("no scent" in failure for failure in played.audit.failures)
    def test_the_downgrade_exists_and_is_explicit(self) -> None:
        game, _ = a_subgame(ScentedOpponent(omit=True))
        game.require_bound_scent = False
        played = game.play()
        assert played.audit.clean, str(played.audit)
    def test_the_crypto_verdict_is_still_reported_alongside(self) -> None:
        game, _ = a_subgame(ScentedOpponent(forge_at=1))
        played = game.play()
        assert played.audit.checked == 3
