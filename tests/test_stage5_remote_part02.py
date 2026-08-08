from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_stage5_remote")).items() if not k.startswith("__")})

class TestSurvivingATunnelRestartMidSeries:
    def test_the_series_continues_at_the_new_address(
        self, wired: tuple[Internet, Orchestrator, Orchestrator], tmp_path: Path
    ) -> None:
        net, cop, thief = wired
        thief.announce(thief.greeting(THIEF_URL, "them"))
        first = cop.open_series(cop.greeting(COP_URL, "s82kma9e"), tmp_path, "g1")
        assert cop.call_opponent("receive_turn", {"message": TURN})["ok"] is True
        del net.hosts[THIEF_URL]
        net.listen(MOVED_THIEF_URL, thief)
        thief.announce(thief.greeting(MOVED_THIEF_URL, "them"))
        second = cop.rehandshake(first, cop.greeting(COP_URL, "s82kma9e"), 2, tmp_path, "g1")
        assert second.theirs.public_url == MOVED_THIEF_URL
        assert cop.call_opponent("receive_turn", {"message": {**TURN, "step": 2}})["ok"] is True
        assert net.delivered[-1] == (MOVED_THIEF_URL, "receive_turn")
    def test_without_the_re_handshake_the_old_address_is_dead(
        self, wired: tuple[Internet, Orchestrator, Orchestrator], tmp_path: Path
    ) -> None:
        net, cop, thief = wired
        thief.announce(thief.greeting(THIEF_URL, "them"))
        cop.open_series(cop.greeting(COP_URL, "s82kma9e"), tmp_path, "g1")
        del net.hosts[THIEF_URL]
        net.listen(MOVED_THIEF_URL, thief)
        with pytest.raises(MatchAborted):
            cop.call_opponent("receive_turn", {"message": TURN})
    def test_our_own_tunnel_moving_is_survivable_the_other_way_round(
        self, wired: tuple[Internet, Orchestrator, Orchestrator], tmp_path: Path
    ) -> None:
        net, cop, thief = wired
        thief.announce(thief.greeting(THIEF_URL, "them"))
        first = cop.open_series(cop.greeting(COP_URL, "s82kma9e"), tmp_path, "g1")
        theirs = Peering(
            thief.greeting(THIEF_URL, "them"),
            Greeting("police", "s82kma9e", COP_URL, PROTOCOL_VERSION),
            sub_game=1,
        )
        del net.hosts[COP_URL]
        net.listen(MOVED_COP_URL, cop)
        moved = cop.greeting(MOVED_COP_URL, "s82kma9e")
        assert cop.try_announce(moved) is True
        thief.rehandshake(theirs, thief.greeting(THIEF_URL, "them"), 2, tmp_path, "g2")
        assert thief.client.opponent_url == MOVED_COP_URL
        assert "announce-failed" in thief.heartbeats
        second = cop.rehandshake(first, moved, 2, tmp_path, "g1")
        assert second.ours.public_url == MOVED_COP_URL
    def test_both_tunnels_rotating_at_once_is_a_clean_timeout(
        self, wired: tuple[Internet, Orchestrator, Orchestrator], tmp_path: Path
    ) -> None:
        net, cop, thief = wired
        thief.announce(thief.greeting(THIEF_URL, "them"))
        first = cop.open_series(cop.greeting(COP_URL, "s82kma9e"), tmp_path, "g1")
        net.hosts.clear()
        with pytest.raises(MatchAborted) as excinfo:
            cop.rehandshake(
                first, cop.greeting(MOVED_COP_URL, "s82kma9e"), 2, tmp_path, "g1", timeout=0.0
            )
        assert excinfo.value.cause is TechnicalLoss.TIMEOUT
        assert "announce-failed" in cop.heartbeats
    def test_the_declaration_says_which_sub_game_the_move_took_effect(
        self, wired: tuple[Internet, Orchestrator, Orchestrator], tmp_path: Path
    ) -> None:
        net, cop, thief = wired
        thief.announce(thief.greeting(THIEF_URL, "them"))
        first = cop.open_series(cop.greeting(COP_URL, "s82kma9e"), tmp_path, "g1")
        net.listen(MOVED_THIEF_URL, thief)
        thief.announce(thief.greeting(MOVED_THIEF_URL, "them"))
        cop.rehandshake(first, cop.greeting(COP_URL, "s82kma9e"), 2, tmp_path, "g1")
        written = json.loads((tmp_path / "declaration_g1.json").read_text())
        assert written[ADDRESS_KEY]["thief"]["since_sub_game"] == 2
        assert written[ADDRESS_KEY]["police"]["public_url"] == COP_URL
