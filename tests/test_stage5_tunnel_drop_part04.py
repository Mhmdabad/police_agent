from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_stage5_tunnel_drop")).items() if not k.startswith("__")})

class TestTheLogTellsTheStory:
    def dropped(self) -> Orchestrator:
        tunnel = Tunnel()
        orch = peer(tunnel)
        orch.call_opponent("receive_turn", TURN)
        tunnel.kill()
        with pytest.raises(MatchAborted):
            orch.call_opponent("receive_turn", {**TURN, "step": 5})
        return orch
    def test_it_shows_the_tunnel_alive_then_gone(self) -> None:
        log = self.dropped().client.log
        assert [event.kind for event in log.events] == [
            SENT,
            CONNECT,
            SENT,
            TIMEOUT,
            RETRY,
            TIMEOUT,
            RETRY,
            TIMEOUT,
            RETRY,
            TIMEOUT,
            UNREACHABLE,
        ]
    def test_the_summary_is_readable_by_a_person(self) -> None:
        rendered = self.dropped().client.log.render()
        assert "unreachable 1" in rendered
        assert "is gone" in rendered
    def test_it_can_be_written_beside_the_match(self, tmp_path: Path) -> None:
        path = self.dropped().client.log.write(tmp_path / "transport_g1_g01.log")
        assert LIVE_URL in path.read_text()
