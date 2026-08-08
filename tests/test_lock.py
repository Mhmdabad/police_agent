import dataclasses
import json
from cop_agent.domain.fixture import BINDING, build
from cop_agent.domain.lock import SOURCE_OFFER, ScentLock, agreed, compare, propose
from cop_agent.domain.scent import CHEBYSHEV
class TestTheAgreementIsOverNumbers:
    def test_two_peers_running_the_same_model_agree(self) -> None:
        assert agreed(propose(), propose().terms())
        assert compare(propose(), propose().terms()) == []
    def test_the_digest_is_stable(self) -> None:
        assert propose().digest() == propose().digest()
    def test_a_different_falloff_changes_the_digest(self) -> None:
        assert propose().digest() != propose(CHEBYSHEV).digest()
    def test_it_covers_the_worked_example_not_only_the_parameters(self) -> None:
        canonical = propose().canonical().decode()
        assert "0.81" in canonical
        assert "decay_series" in canonical and "emission" in canonical
    def test_the_offer_text_is_outside_the_digest(self) -> None:
        reworded = ScentLock(fixture=propose().fixture, source_offer="different words")
        assert reworded.digest() == propose().digest()
class TestDisagreementIsReportedNotResolved:
    def test_a_chebyshev_peer_is_named_term_by_term(self) -> None:
        problems = compare(propose(), propose(CHEBYSHEV).terms())
        assert problems
        assert any(problem.startswith("emission:") for problem in problems)
        assert any(problem.startswith("model:") for problem in problems)
    def test_our_model_is_not_quietly_adopted(self) -> None:
        ours = propose()
        before = ours.digest()
        compare(ours, propose(CHEBYSHEV).terms())
        assert ours.digest() == before
        assert not agreed(ours, propose(CHEBYSHEV).terms())
    def test_a_decay_disagreement_is_caught_even_when_emission_matches(self) -> None:
        theirs = propose().terms()
        model = theirs["scent_model"]
        assert isinstance(model, dict)
        model["decay_series"] = [0.80, 0.70, 0.60]
        problems = compare(propose(), theirs)
        assert len(problems) == 1
        assert problems[0].startswith("decay_series:")
    def test_a_missing_term_is_reported(self) -> None:
        theirs = propose().terms()
        model = theirs["scent_model"]
        assert isinstance(model, dict)
        del model["decay_rate"]
        assert compare(propose(), theirs) == ["decay_rate: absent from their proposal"]
    def test_an_unrecognised_term_is_reported(self) -> None:
        theirs = propose().terms()
        model = theirs["scent_model"]
        assert isinstance(model, dict)
        model["wind_direction"] = "north"
        assert compare(propose(), theirs) == ["wind_direction: not a term we recognise"]
    def test_a_malformed_proposal_is_refused_rather_than_crashing(self) -> None:
        assert compare(propose(), {}) == ["scent_model: missing or malformed"]
        assert compare(propose(), {"scent_model": "trust me"}) == [
            "scent_model: missing or malformed"
        ]
    def test_every_disagreement_is_listed_at_once(self) -> None:
        assert len(compare(propose(), propose(CHEBYSHEV).terms())) >= 2
class TestTheBindingIsPartOfTheAgreement:
    def test_the_proposal_names_how_the_field_is_bound(self) -> None:
        model = propose().terms()["scent_model"]
        assert isinstance(model, dict)
        assert model["binding"] == BINDING
    def test_the_binding_names_the_phase_and_the_commitment(self) -> None:
        assert "commit" in BINDING and "reveal" in BINDING
    def test_it_is_covered_by_the_digest(self) -> None:
        theirs = dataclasses.replace(build(), binding="turn-message-unbound")
        assert ScentLock(fixture=theirs).digest() != propose().digest()
    def test_a_peer_that_cannot_bind_its_scent_is_named(self) -> None:
        theirs = propose().terms()
        model = theirs["scent_model"]
        assert isinstance(model, dict)
        model["binding"] = "turn-message-unbound"
        problems = compare(propose(), theirs)
        assert len(problems) == 1
        assert problems[0].startswith("binding:")
        assert not agreed(propose(), theirs)
    def test_a_peer_that_omits_it_entirely_is_named(self) -> None:
        theirs = propose().terms()
        model = theirs["scent_model"]
        assert isinstance(model, dict)
        del model["binding"]
        assert compare(propose(), theirs) == ["binding: absent from their proposal"]
class TestTheCodeOffer:
    def test_it_accompanies_the_proposal(self) -> None:
        assert propose().terms()["source_offer"] == SOURCE_OFFER
    def test_it_names_the_modules(self) -> None:
        for module in ("domain/scent.py", "domain/trail.py", "domain/fixture.py"):
            assert module in SOURCE_OFFER
    def test_it_says_why_it_costs_nothing(self) -> None:
        assert "public and symmetric" in SOURCE_OFFER
class TestItCrossesTheWire:
    def test_the_payload_is_json_safe(self) -> None:
        assert json.loads(json.dumps(propose().terms()))["source_offer"] == SOURCE_OFFER
    def test_a_round_trip_still_agrees(self) -> None:
        wire = json.loads(json.dumps(propose().terms()))
        assert agreed(propose(), wire)
    def test_the_canonical_bytes_are_what_is_hashed(self) -> None:
        assert propose().canonical() == propose().canonical()
        assert b'"scent_model"' in propose().canonical()
