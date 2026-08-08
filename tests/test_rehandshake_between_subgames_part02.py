from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_rehandshake_between_subgames")).items() if not k.startswith("__")})

class TestARotatedAddressReachesTheTransportTheNextSubGameUses:
    def rotating_after(self, number: int, transport: ScriptedPeer) -> Callable[[int], None]:
        def rotate(played: int) -> None:
            if played == number:
                transport.announce = greets(ROTATED)
        return rotate
    def test_the_next_sub_games_first_commit_goes_to_the_new_address(
        self, tmp_path: Path, stub: Install
    ) -> None:
        transport = ScriptedPeer(PeerInboxes())
        stub(self.rotating_after(2, transport))
        runner = opened(tmp_path, transport)
        runner.play_series(timeout=1.0)
        assert transport.where("receive_turn") == [AT_THEIRS] * 2 + [AT_ROTATED] * 4
    def test_the_client_is_re_pointed_before_that_commit_rather_than_after(
        self, tmp_path: Path, stub: Install
    ) -> None:
        transport = ScriptedPeer(PeerInboxes())
        stub(self.rotating_after(2, transport))
        runner = opened(tmp_path, transport)
        runner.play_series(timeout=1.0)
        moved = transport.calls.index((AT_ROTATED, "receive_turn"))
        assert transport.calls[moved - 1] == (AT_THEIRS, "negotiate")
        assert runner.orchestrator.client.opponent_url == AT_ROTATED
    def test_the_relocation_is_recorded_once_where_a_dispute_can_read_it(
        self, tmp_path: Path, stub: Install
    ) -> None:
        transport = ScriptedPeer(PeerInboxes())
        stub(self.rotating_after(2, transport))
        runner = opened(tmp_path, transport)
        runner.play_series(timeout=1.0)
        assert runner.orchestrator.client.relocations[-1] == (AT_THEIRS, AT_ROTATED)
        assert any(
            beat.startswith(f"agreed-move:{OPPONENT}:") for beat in runner.orchestrator.heartbeats
        )
    def test_the_declaration_says_which_sub_game_the_new_address_took_effect_at(
        self, tmp_path: Path, stub: Install
    ) -> None:
        transport = ScriptedPeer(PeerInboxes())
        stub(self.rotating_after(2, transport))
        runner = opened(tmp_path, transport)
        runner.play_series(timeout=1.0)
        written = json.loads((tmp_path / f"declaration_{GAME_ID}.json").read_text())
        assert written["mcp_addresses"][OPPONENT]["public_url"] == AT_ROTATED
        assert written["mcp_addresses"][OPPONENT]["since_sub_game"] == BOOK_SERIES
    def test_one_client_session_is_kept_per_active_endpoint(
        self, tmp_path: Path, stub: Install
    ) -> None:
        transport = ScriptedPeer(PeerInboxes())
        stub(self.rotating_after(2, transport))
        runner = opened(tmp_path, transport)
        client = runner.orchestrator.client
        runner.play_series(timeout=1.0)
        assert runner.orchestrator.client is client
        assert client.relocations == [(AT_THEIRS, AT_ROTATED)]  # one move, five boundaries
