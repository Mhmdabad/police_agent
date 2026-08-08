from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_stage5_remote")).items() if not k.startswith("__")})

class TestAFullRoundOverPublicAddresses:
    def test_both_peers_are_addressed_by_a_public_url(
        self, wired: tuple[Internet, Orchestrator, Orchestrator]
    ) -> None:
        net, _, _ = wired
        assert set(net.hosts) == {COP_URL, THIEF_URL}
        assert not any("127.0.0.1" in url or "localhost" in url for url in net.hosts)
    def test_the_handshake_completes_and_the_declaration_names_both(
        self, wired: tuple[Internet, Orchestrator, Orchestrator], tmp_path: Path
    ) -> None:
        net, cop, thief = wired
        ours, theirs = cop.greeting(COP_URL, "s82kma9e"), thief.greeting(THIEF_URL, "them")
        cop.announce(ours)
        thief.announce(theirs)
        peering = cop.open_series(ours, tmp_path, "uoh26-s82kma9e")
        assert peering.sub_game == 1
        written = json.loads((tmp_path / "declaration_uoh26-s82kma9e.json").read_text())
        assert written[ADDRESS_KEY]["police"]["public_url"] == COP_URL
        assert written[ADDRESS_KEY]["thief"]["public_url"] == THIEF_URL
        assert all(entry["reachable"] for entry in written[ADDRESS_KEY].values())
    def test_a_turn_crosses_the_network_and_lands_in_the_mailbox(
        self, wired: tuple[Internet, Orchestrator, Orchestrator]
    ) -> None:
        net, cop, thief = wired
        assert thief.call_opponent("receive_turn", {"message": TURN})["ok"] is True
        assert net.delivered == [(COP_URL, "receive_turn")]
        assert cop.inboxes.turns.get_nowait().hint == "heading for the water"
    def test_a_full_round_completes_with_no_loopback_traffic(
        self, wired: tuple[Internet, Orchestrator, Orchestrator], tmp_path: Path
    ) -> None:
        net, cop, thief = wired
        thief.announce(thief.greeting(THIEF_URL, "them"))
        cop.open_series(cop.greeting(COP_URL, "s82kma9e"), tmp_path, "g1")
        for step in range(1, 6):
            assert (
                thief.call_opponent("receive_turn", {"message": {**TURN, "step": step}})["ok"]
                is True
            )
            assert cop.inboxes.turns.get_nowait().step == step
        assert [url for url, _ in net.delivered] == [COP_URL, THIEF_URL] + [COP_URL] * 5
    def test_a_dropped_tunnel_is_a_recorded_abort_rather_than_a_hang(
        self, wired: tuple[Internet, Orchestrator, Orchestrator]
    ) -> None:
        net, cop, _ = wired
        del net.hosts[THIEF_URL]
        with pytest.raises(MatchAborted, match="nothing answers|after 4 attempts"):
            cop.call_opponent("receive_turn", {"message": TURN})
