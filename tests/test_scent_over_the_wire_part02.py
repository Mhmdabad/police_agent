from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_scent_over_the_wire")).items() if not k.startswith("__")})

class TestNothingIsGivenAwayInPhaseOne:
    def test_the_commitment_carries_no_field(self, played: tuple[Side, Side]) -> None:
        cop, _ = played
        for step in range(1, STEPS + 1):
            commitment = cop.game.ceremony.at(step).ours
            assert commitment is not None
            assert "scent" not in commitment.to_dict()
    def test_the_turn_message_we_put_on_the_wire_has_an_empty_smell_grid(self) -> None:
        sent: list[tuple[str, dict[str, Any]]] = []
        class Recorder:
            def call(
                self, url: str, tool: str, payload: dict[str, Any], timeout: float
            ) -> dict[str, Any]:
                sent.append((tool, payload))
                return {"ok": True}
        peer = McpPeer(
            role="police",
            client=OpponentClient(
                Recorder(), ClientSettings(opponent_url="http://127.0.0.1:1/mcp")
            ),
            inboxes=PeerInboxes(),
            game_uid="u-0001",
            sub_game=1,
            now=WHEN,
        )
        peer.send_commit(Commitment(step=1, sender="police", commit="a" * 64, timestamp=WHEN))
        tool, payload = sent[0]
        assert tool == "receive_turn"
        assert payload["message"]["hint"] == ""
        assert payload["message"]["smell_grid"] == {}
    def test_no_nonce_travels_with_the_field(self, played: tuple[Side, Side]) -> None:
        cop, _ = played
        for step in range(1, STEPS + 1):
            opened = cop.game.ceremony.at(step).revealed_theirs
            assert opened is not None
            assert "nonce" not in json.dumps(opened.to_dict())
