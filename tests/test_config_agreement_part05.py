from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_config_agreement")).items() if not k.startswith("__")})

class TestOnlyAWellFormedCurrentDigestSatisfiesTheGate:
    @pytest.mark.parametrize(
        "value",
        ["", "not-a-digest", "a" * 63, "a" * 65, "z" * 64, 0, True, None, ["a" * 64]],
    )
    def test_a_malformed_digest_is_refused_at_the_door(
        self, wire: tuple[Side, Side], value: object
    ) -> None:
        ours, theirs = fresh(wire)
        assert theirs.send({"config_sha256": value})["ok"] is False
        assert ours.inboxes.digests.empty()
        assert ours.inboxes.rejected
    def test_a_refused_digest_cannot_satisfy_the_gate(self, wire: tuple[Side, Side]) -> None:
        ours, theirs = fresh(wire)
        theirs.send({"config_sha256": "not-a-digest"})
        with pytest.raises(MatchAborted) as excinfo:
            ours.orchestrator.agree_config(parameters(), game_uid=GAME_UID, timeout=BRIEF)
        assert excinfo.value.cause is TechnicalLoss.TIMEOUT
    def test_a_digest_bound_to_another_series_does_not_answer_this_one(
        self, wire: tuple[Side, Side]
    ) -> None:
        ours, theirs = fresh(wire)
        theirs.send({"config_sha256": agreed_digest(), "game_uid": OTHER_UID})
        with pytest.raises(MatchAborted) as excinfo:
            ours.orchestrator.agree_config(parameters(), game_uid=GAME_UID, timeout=BRIEF)
        assert excinfo.value.cause is TechnicalLoss.TIMEOUT
    def test_a_digest_bound_to_this_series_does_answer_it(self, wire: tuple[Side, Side]) -> None:
        ours, theirs = fresh(wire)
        theirs.send({"config_sha256": agreed_digest(), "game_uid": GAME_UID})
        assert (
            ours.orchestrator.agree_config(parameters(), game_uid=GAME_UID, timeout=BRIEF)
            == agreed_digest()
        )
    def test_an_unbound_digest_is_still_accepted(self, wire: tuple[Side, Side]) -> None:
        ours, theirs = fresh(wire)
        theirs.send({"config_sha256": agreed_digest()})
        assert (
            ours.orchestrator.agree_config(parameters(), game_uid=GAME_UID, timeout=BRIEF)
            == agreed_digest()
        )
    def test_an_identical_retry_is_not_a_disagreement(self, wire: tuple[Side, Side]) -> None:
        ours, theirs = fresh(wire)
        for _ in range(2):
            theirs.send({"config_sha256": agreed_digest(), "game_uid": GAME_UID})
        assert (
            ours.orchestrator.agree_config(parameters(), game_uid=GAME_UID, timeout=BRIEF)
            == agreed_digest()
        )
    def test_a_duplicate_cannot_mask_a_disagreement_behind_it(
        self, wire: tuple[Side, Side]
    ) -> None:
        ours, theirs = fresh(wire)
        theirs.send({"config_sha256": agreed_digest(), "game_uid": GAME_UID})
        theirs.send({"config_sha256": agreed_digest(), "game_uid": GAME_UID})
        theirs.send({"config_sha256": config_sha256(altered()), "game_uid": GAME_UID})
        with pytest.raises(MatchAborted) as excinfo:
            ours.orchestrator.agree_config(parameters(), game_uid=GAME_UID, timeout=BRIEF)
        assert excinfo.value.cause is TechnicalLoss.ILLEGAL_ACTION
    def test_a_consumed_digest_does_not_open_the_next_series(self, wire: tuple[Side, Side]) -> None:
        ours, theirs = fresh(wire)
        theirs.send({"config_sha256": agreed_digest(), "game_uid": GAME_UID})
        ours.orchestrator.agree_config(parameters(), game_uid=GAME_UID, timeout=BRIEF)
        with pytest.raises(MatchAborted) as excinfo:
            ours.orchestrator.agree_config(parameters(), game_uid=GAME_UID, timeout=BRIEF)
        assert excinfo.value.cause is TechnicalLoss.TIMEOUT
    def test_an_uppercase_spelling_is_the_same_digest(self, wire: tuple[Side, Side]) -> None:
        ours, theirs = fresh(wire)
        theirs.send({"config_sha256": agreed_digest().upper(), "game_uid": GAME_UID})
        assert (
            ours.orchestrator.agree_config(parameters(), game_uid=GAME_UID, timeout=BRIEF)
            == agreed_digest()
        )
    def test_a_greeting_is_not_a_digest(self, wire: tuple[Side, Side]) -> None:
        ours, theirs = fresh(wire)
        theirs.send(
            {
                "greeting": {
                    "role": THEIR_ROLE,
                    "group_id": "them",
                    "public_url": "https://peer-c3d4.ngrok-free.app",
                    "protocol_version": "1.0",
                }
            }
        )
        with pytest.raises(MatchAborted) as excinfo:
            ours.orchestrator.agree_config(parameters(), game_uid=GAME_UID, timeout=BRIEF)
        assert excinfo.value.cause is TechnicalLoss.TIMEOUT
