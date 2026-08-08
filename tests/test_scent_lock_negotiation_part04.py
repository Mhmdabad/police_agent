from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_scent_lock_negotiation")).items() if not k.startswith("__")})

class TestTheDigestIsTheBinding:
    def test_our_digest_over_their_physics_is_refused(self, wire: tuple[Side, Side]) -> None:
        ours, theirs = fresh(wire)
        theirs.send(an_offer({"model": "chebyshev"}, digest=propose().digest()))
        with pytest.raises(MatchAborted) as excinfo:
            ours.orchestrator.agree_scent_model(game_uid=GAME_UID, timeout=BRIEF)
        assert excinfo.value.cause is TechnicalLoss.ILLEGAL_ACTION
        assert SCENT_DIGEST_KEY in excinfo.value.detail
    def test_their_physics_under_a_digest_of_nothing_is_refused(
        self, wire: tuple[Side, Side]
    ) -> None:
        ours, theirs = fresh(wire)
        theirs.send(an_offer(digest="0" * 64))
        with pytest.raises(MatchAborted) as excinfo:
            ours.orchestrator.agree_scent_model(game_uid=GAME_UID, timeout=BRIEF)
        assert excinfo.value.cause is TechnicalLoss.ILLEGAL_ACTION
    def test_an_uppercase_spelling_is_the_same_digest(self, wire: tuple[Side, Side]) -> None:
        ours, theirs = fresh(wire)
        theirs.send(an_offer(digest=propose().digest().upper()))
        assert ours.orchestrator.agree_scent_model(game_uid=GAME_UID, timeout=BRIEF) == our_lock()
    def test_the_comparison_does_not_leak_a_common_prefix(self) -> None:
        import cop_agent.domain.lock as module
        assert "digests_agree" in Path(module.__file__ or "").read_text()
