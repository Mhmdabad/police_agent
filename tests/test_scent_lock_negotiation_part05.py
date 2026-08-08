from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_scent_lock_negotiation")).items() if not k.startswith("__")})

class TestOnlyAWellFormedCurrentOfferSatisfiesTheGate:
    def test_a_peer_that_offers_no_lock_produces_a_timeout(self, wire: tuple[Side, Side]) -> None:
        ours, _ = fresh(wire)
        with pytest.raises(MatchAborted) as excinfo:
            ours.orchestrator.agree_scent_model(game_uid=GAME_UID, timeout=BRIEF)
        assert excinfo.value.cause is TechnicalLoss.TIMEOUT
    def test_the_opponent_acknowledged_us_all_the_same(self, wire: tuple[Side, Side]) -> None:
        ours, theirs = fresh(wire)
        with pytest.raises(MatchAborted):
            ours.orchestrator.agree_scent_model(game_uid=GAME_UID, timeout=BRIEF)
        assert theirs.inboxes.scent_locks.qsize() == 1
    @pytest.mark.parametrize(
        "body",
        [
            {SCENT_KEY: "trust me", SCENT_DIGEST_KEY: "a" * 64, SERIES_KEY: GAME_UID},
            {
                SCENT_KEY: {"scent_model": "trust me"},
                SCENT_DIGEST_KEY: "a" * 64,
                SERIES_KEY: GAME_UID,
            },
            {SCENT_KEY: {}, SCENT_DIGEST_KEY: "a" * 64, SERIES_KEY: GAME_UID},
            {SCENT_KEY: propose().terms(), SCENT_DIGEST_KEY: "not-a-digest", SERIES_KEY: GAME_UID},
            {SCENT_KEY: propose().terms(), SERIES_KEY: GAME_UID},
            {SCENT_KEY: propose().terms(), SCENT_DIGEST_KEY: "a" * 64, SERIES_KEY: ""},
        ],
    )
    def test_a_malformed_offer_is_refused_at_the_door(
        self, wire: tuple[Side, Side], body: dict[str, Any]
    ) -> None:
        ours, theirs = fresh(wire)
        assert theirs.send(body)["ok"] is False
        assert ours.inboxes.scent_locks.empty()
        assert ours.inboxes.rejected
    def test_a_legacy_offer_naming_no_series_is_refused(self, wire: tuple[Side, Side]) -> None:
        ours, theirs = fresh(wire)
        assert theirs.send(an_offer(uid=None))["ok"] is False
        with pytest.raises(MatchAborted) as excinfo:
            ours.orchestrator.agree_scent_model(game_uid=GAME_UID, timeout=BRIEF)
        assert excinfo.value.cause is TechnicalLoss.TIMEOUT
    def test_an_offer_the_opponent_refuses_aborts_our_side_too(
        self, wire: tuple[Side, Side]
    ) -> None:
        ours, theirs = fresh(wire)
        with pytest.raises(MatchAborted) as excinfo:
            ours.orchestrator.agree_scent_model(game_uid="", timeout=BRIEF)
        assert excinfo.value.cause is TechnicalLoss.ILLEGAL_ACTION
        assert SERIES_KEY in excinfo.value.detail
        assert theirs.inboxes.scent_locks.empty()
    def test_a_refused_offer_cannot_satisfy_the_gate(self, wire: tuple[Side, Side]) -> None:
        ours, theirs = fresh(wire)
        theirs.send({SCENT_KEY: {"scent_model": "trust me"}, SCENT_DIGEST_KEY: "a" * 64})
        with pytest.raises(MatchAborted) as excinfo:
            ours.orchestrator.agree_scent_model(game_uid=GAME_UID, timeout=BRIEF)
        assert excinfo.value.cause is TechnicalLoss.TIMEOUT
    def test_an_offer_bound_to_another_series_does_not_answer_this_one(
        self, wire: tuple[Side, Side]
    ) -> None:
        ours, theirs = fresh(wire)
        theirs.send(an_offer(uid=OTHER_UID))
        with pytest.raises(MatchAborted) as excinfo:
            ours.orchestrator.agree_scent_model(game_uid=GAME_UID, timeout=BRIEF)
        assert excinfo.value.cause is TechnicalLoss.TIMEOUT
    def test_an_offer_bound_to_this_series_does_answer_it(self, wire: tuple[Side, Side]) -> None:
        ours, theirs = fresh(wire)
        theirs.send(an_offer())
        assert ours.orchestrator.agree_scent_model(game_uid=GAME_UID, timeout=BRIEF) == our_lock()
    def test_an_identical_retry_is_not_a_disagreement(self, wire: tuple[Side, Side]) -> None:
        ours, theirs = fresh(wire)
        for _ in range(2):
            theirs.send(an_offer())
        assert ours.orchestrator.agree_scent_model(game_uid=GAME_UID, timeout=BRIEF) == our_lock()
    def test_a_duplicate_cannot_mask_a_conflicting_offer_behind_it(
        self, wire: tuple[Side, Side]
    ) -> None:
        ours, theirs = fresh(wire)
        theirs.send(an_offer())
        theirs.send(an_offer())
        theirs.send(an_offer({"decay_rate": 0.2}))
        with pytest.raises(MatchAborted) as excinfo:
            ours.orchestrator.agree_scent_model(game_uid=GAME_UID, timeout=BRIEF)
        assert excinfo.value.cause is TechnicalLoss.ILLEGAL_ACTION
    def test_a_stale_offer_queued_behind_a_good_one_is_still_dropped(
        self, wire: tuple[Side, Side]
    ) -> None:
        ours, theirs = fresh(wire)
        theirs.send(an_offer())
        theirs.send(an_offer({"decay_rate": 0.2}, uid=OTHER_UID))
        assert ours.orchestrator.agree_scent_model(game_uid=GAME_UID, timeout=BRIEF) == our_lock()
    def test_a_consumed_offer_does_not_open_the_next_series(self, wire: tuple[Side, Side]) -> None:
        ours, theirs = fresh(wire)
        theirs.send(an_offer())
        ours.orchestrator.agree_scent_model(game_uid=GAME_UID, timeout=BRIEF)
        with pytest.raises(MatchAborted) as excinfo:
            ours.orchestrator.agree_scent_model(game_uid=GAME_UID, timeout=BRIEF)
        assert excinfo.value.cause is TechnicalLoss.TIMEOUT
    def test_a_greeting_is_not_an_offer(self, wire: tuple[Side, Side]) -> None:
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
            ours.orchestrator.agree_scent_model(game_uid=GAME_UID, timeout=BRIEF)
        assert excinfo.value.cause is TechnicalLoss.TIMEOUT
    def test_a_config_digest_is_not_an_offer(self, wire: tuple[Side, Side]) -> None:
        ours, theirs = fresh(wire)
        theirs.send({"config_sha256": "a" * 64, SERIES_KEY: GAME_UID})
        assert ours.inboxes.scent_locks.empty()
        assert ours.inboxes.digests.qsize() == 1
