from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_rehandshake_between_subgames")).items() if not k.startswith("__")})

class TestOnlyTheAddressMayMoveAcrossABoundary:
    @pytest.mark.parametrize(
        "changed",
        [{"role": ROLE}, {"group_id": "someone-else"}, {"protocol_version": "9.9"}],
        ids=["role", "group", "protocol"],
    )
    def test_an_identity_change_is_refused_rather_than_followed(
        self, tmp_path: Path, stub: Install, changed: dict[str, str]
    ) -> None:
        transport = ScriptedPeer(PeerInboxes())
        def swap(played: int) -> None:
            if played == 2:
                transport.announce = greets(ROTATED, **changed)
        stub(swap)
        runner = opened(tmp_path, transport)
        with pytest.raises(MatchAborted) as excinfo:
            runner.play_series(timeout=1.0)
        assert excinfo.value.cause is TechnicalLoss.ILLEGAL_ACTION
        assert [o.number for o in runner.outcomes] == [1, 2]
    @pytest.mark.parametrize(
        "changed",
        [{"role": ROLE}, {"group_id": "someone-else"}, {"protocol_version": "9.9"}],
        ids=["role", "group", "protocol"],
    )
    def test_a_refused_boundary_leaves_the_client_where_it_was(
        self, tmp_path: Path, stub: Install, changed: dict[str, str]
    ) -> None:
        transport = ScriptedPeer(PeerInboxes())
        def swap(played: int) -> None:
            if played == 2:
                transport.announce = greets(ROTATED, **changed)
        stub(swap)
        runner = opened(tmp_path, transport)
        with pytest.raises(MatchAborted):
            runner.play_series(timeout=1.0)
        assert runner.orchestrator.client.opponent_url == AT_THEIRS
        assert runner.peering is not None and runner.peering.sub_game == 2
    def test_a_config_digest_is_not_a_greeting_and_does_not_rotate_anything(
        self, tmp_path: Path, stub: Install
    ) -> None:
        transport = ScriptedPeer(PeerInboxes())
        def swap(played: int) -> None:
            if played == 1:
                transport.announce = {
                    DIGEST_KEY: config_sha256(parameters()),
                    SERIES_KEY: GAME_UID,
                }
        stub(swap)
        runner = opened(tmp_path, transport)
        with pytest.raises(MatchAborted) as excinfo:
            runner.play_series(timeout=0.05)
        assert excinfo.value.cause is TechnicalLoss.TIMEOUT
        assert runner.orchestrator.client.opponent_url == AT_THEIRS
    def test_a_scent_lock_offer_is_not_a_greeting_either(
        self, tmp_path: Path, stub: Install
    ) -> None:
        transport = ScriptedPeer(PeerInboxes())
        def swap(played: int) -> None:
            if played == 1:
                transport.announce = {
                    SCENT_KEY: {"scent_model": {"emission": {}}},
                    SCENT_DIGEST_KEY: "b" * 64,
                    SERIES_KEY: GAME_UID,
                }
        stub(swap)
        runner = opened(tmp_path, transport)
        with pytest.raises(MatchAborted) as excinfo:
            runner.play_series(timeout=0.05)
        assert excinfo.value.cause is TechnicalLoss.TIMEOUT
        assert runner.orchestrator.client.opponent_url == AT_THEIRS
