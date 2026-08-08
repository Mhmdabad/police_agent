from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_orchestrator")).items() if not k.startswith("__")})

class TestExchangingAddresses:
    def test_it_announces_before_it_waits(self, tmp_path: Path) -> None:
        orch, transport = orchestrator()
        inbound(orch)
        orch.open_series(orch.greeting(OUR_URL, "s82kma9e"), tmp_path, "g1")
        assert [c["tool"] for c in transport.calls] == ["negotiate"]
    def test_it_writes_both_addresses_into_the_declaration(self, tmp_path: Path) -> None:
        orch, _ = orchestrator()
        inbound(orch)
        peering = orch.open_series(orch.greeting(OUR_URL, "s82kma9e"), tmp_path, "g1")
        assert peering.sub_game == 1
        written = json.loads((tmp_path / "declaration_g1.json").read_text())
        assert written["mcp_addresses"]["police"]["public_url"] == f"{OUR_URL}/mcp"
        assert written["mcp_addresses"]["thief"]["public_url"] == f"{THEIR_URL}/mcp"
    def test_a_refused_greeting_writes_no_declaration(self, tmp_path: Path) -> None:
        orch, _ = orchestrator()
        inbound(orch, role="police")
        with pytest.raises(MatchAborted):
            orch.open_series(orch.greeting(OUR_URL, "s82kma9e"), tmp_path, "g1")
        assert not (tmp_path / "declaration_g1.json").exists()
