from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_orchestrator")).items() if not k.startswith("__")})

class TestSurvivingARotatedTunnel:
    def opened(self, tmp_path: Path, *outcomes: object) -> tuple[Orchestrator, Peering]:
        orch, _ = orchestrator(*outcomes)
        inbound(orch)
        return orch, orch.open_series(orch.greeting(OUR_URL, "s82kma9e"), tmp_path, "g1")
    def test_the_opening_handshake_adopts_the_announced_address(self, tmp_path: Path) -> None:
        orch, _ = self.opened(tmp_path)
        assert orch.client.opponent_url == f"{THEIR_URL}/mcp"
        assert orch.client.relocations == [("http://127.0.0.1:8802/mcp", f"{THEIR_URL}/mcp")]
    def test_an_unchanged_address_re_handshakes_quietly(self, tmp_path: Path) -> None:
        orch, first = self.opened(tmp_path)
        inbound(orch)
        second = orch.rehandshake(first, orch.greeting(OUR_URL, "s82kma9e"), 2, tmp_path, "g1")
        assert second.sub_game == 2
        assert len(orch.client.relocations) == 1  # the opening adoption, nothing since
    def test_a_failed_announcement_is_tolerated_then_retried_at_the_new_address(
        self, tmp_path: Path
    ) -> None:
        orch, first = self.opened(tmp_path, {"ok": True}, *[ConnectionError()] * 4)
        inbound(orch, url=ROTATED)
        orch.rehandshake(first, orch.greeting(OUR_URL, "s82kma9e"), 2, tmp_path, "g1")
        assert "announce-failed" in orch.heartbeats
        assert orch.client.opponent_url == f"{ROTATED}/mcp"
    def test_a_new_opponent_url_re_points_the_client(self, tmp_path: Path) -> None:
        orch, first = self.opened(tmp_path)
        inbound(orch, url=ROTATED)
        orch.rehandshake(first, orch.greeting(OUR_URL, "s82kma9e"), 2, tmp_path, "g1")
        assert orch.client.opponent_url == f"{ROTATED}/mcp"
        assert orch.client.relocations[-1] == (f"{THEIR_URL}/mcp", f"{ROTATED}/mcp")
    def test_the_relocation_is_a_heartbeat_so_the_log_can_show_it(self, tmp_path: Path) -> None:
        orch, first = self.opened(tmp_path)
        inbound(orch, url=ROTATED)
        orch.rehandshake(first, orch.greeting(OUR_URL, "s82kma9e"), 2, tmp_path, "g1")
        assert any(b.startswith("agreed-move:thief:") for b in orch.heartbeats)
        assert any(b.startswith("relocated:thief:") for b in orch.heartbeats)
    def test_the_declaration_records_which_sub_game_an_address_took_effect(
        self, tmp_path: Path
    ) -> None:
        orch, first = self.opened(tmp_path)
        inbound(orch, url=ROTATED)
        orch.rehandshake(first, orch.greeting(OUR_URL, "s82kma9e"), 2, tmp_path, "g1")
        written = json.loads((tmp_path / "declaration_g1.json").read_text())
        assert written["mcp_addresses"]["thief"] == {
            "role": "thief",
            "group_id": "them",
            "public_url": f"{ROTATED}/mcp",
            "protocol_version": PROTOCOL_VERSION,
            "reachable": True,
            "since_sub_game": 2,
        }
    def test_a_different_team_at_a_new_address_is_refused(self, tmp_path: Path) -> None:
        orch, first = self.opened(tmp_path)
        orch.inboxes.negotiate(
            {
                "greeting": {
                    "role": "thief",
                    "group_id": "someone-else",
                    "public_url": ROTATED,
                    "protocol_version": PROTOCOL_VERSION,
                }
            }
        )
        with pytest.raises(MatchAborted, match="this is a different peer"):
            orch.rehandshake(first, orch.greeting(OUR_URL, "s82kma9e"), 2, tmp_path, "g1")
        assert orch.client.opponent_url == f"{THEIR_URL}/mcp"
    def test_a_mid_sub_game_address_change_is_refused(self, tmp_path: Path) -> None:
        orch, first = self.opened(tmp_path)
        inbound(orch, url=ROTATED)
        with pytest.raises(MatchAborted, match="only change between sub-games"):
            orch.rehandshake(first, orch.greeting(OUR_URL, "s82kma9e"), 1, tmp_path, "g1")
        assert orch.client.opponent_url == f"{THEIR_URL}/mcp"
    def test_our_own_rotated_address_is_announced_without_re_pointing(self, tmp_path: Path) -> None:
        orch, first = self.opened(tmp_path)
        inbound(orch)
        ours_moved = orch.greeting("https://cop-9z8y.ngrok-free.app", "s82kma9e")
        second = orch.rehandshake(first, ours_moved, 2, tmp_path, "g1")
        assert second.ours.public_url == "https://cop-9z8y.ngrok-free.app/mcp"
        assert len(orch.client.relocations) == 1  # the opening adoption only
    def test_silence_at_re_handshake_is_a_timeout(self, tmp_path: Path) -> None:
        orch, first = self.opened(tmp_path)
        with pytest.raises(MatchAborted) as excinfo:
            orch.rehandshake(
                first, orch.greeting(OUR_URL, "s82kma9e"), 2, tmp_path, "g1", timeout=0.0
            )
        assert excinfo.value.cause is TechnicalLoss.TIMEOUT
