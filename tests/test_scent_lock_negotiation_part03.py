from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_scent_lock_negotiation")).items() if not k.startswith("__")})

class TestAnyDivergenceAbortsTheSeriesBeforePlay:
    @pytest.mark.parametrize("term", sorted(DIVERGENCES))
    def test_one_differing_term_is_fatal(self, wire: tuple[Side, Side], term: str) -> None:
        ours, theirs = fresh(wire)
        theirs.send(an_offer(DIVERGENCES[term]))
        with pytest.raises(MatchAborted) as excinfo:
            ours.orchestrator.agree_scent_model(game_uid=GAME_UID, timeout=BRIEF)
        assert excinfo.value.cause is TechnicalLoss.ILLEGAL_ACTION
    @pytest.mark.parametrize("term", sorted(DIVERGENCES))
    def test_the_differing_term_is_named(self, wire: tuple[Side, Side], term: str) -> None:
        ours, theirs = fresh(wire)
        theirs.send(an_offer(DIVERGENCES[term]))
        with pytest.raises(MatchAborted) as excinfo:
            ours.orchestrator.agree_scent_model(game_uid=GAME_UID, timeout=BRIEF)
        assert next(iter(DIVERGENCES[term])) in excinfo.value.detail
    def test_a_precision_divergence_is_fatal(self, wire: tuple[Side, Side]) -> None:
        ours, theirs = fresh(wire)
        theirs.send(an_offer(finer_precision()))
        with pytest.raises(MatchAborted) as excinfo:
            ours.orchestrator.agree_scent_model(game_uid=GAME_UID, timeout=BRIEF)
        assert excinfo.value.cause is TechnicalLoss.ILLEGAL_ACTION
    def test_the_reference_falloff_is_refused_in_full(self, wire: tuple[Side, Side]) -> None:
        ours, theirs = fresh(wire)
        terms = propose(CHEBYSHEV).terms()
        theirs.send({SCENT_KEY: terms, SCENT_DIGEST_KEY: restate(terms), SERIES_KEY: GAME_UID})
        with pytest.raises(MatchAborted) as excinfo:
            ours.orchestrator.agree_scent_model(game_uid=GAME_UID, timeout=BRIEF)
        assert excinfo.value.cause is TechnicalLoss.ILLEGAL_ACTION
        assert "emission" in excinfo.value.detail and "model" in excinfo.value.detail
    def test_both_sides_abort_when_each_runs_its_own_model(self, wire: tuple[Side, Side]) -> None:
        ours, theirs = fresh(wire)
        done = concurrently(
            {
                "ours": lambda: ours.orchestrator.agree_scent_model(
                    game_uid=GAME_UID, timeout=PATIENCE
                ),
                "theirs": lambda: theirs.orchestrator.agree_scent_model(
                    game_uid=GAME_UID, ours=propose(CHEBYSHEV), timeout=PATIENCE
                ),
            }
        )
        assert [outcome.cause for outcome in done.values()] == [TechnicalLoss.ILLEGAL_ACTION] * 2
    def test_our_model_is_not_quietly_adopted(self, wire: tuple[Side, Side]) -> None:
        ours, theirs = fresh(wire)
        theirs.send(an_offer({"model": "chebyshev"}))
        with pytest.raises(MatchAborted):
            ours.orchestrator.agree_scent_model(game_uid=GAME_UID, timeout=BRIEF)
        assert propose().digest() == our_lock().digest
