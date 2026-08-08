from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_stage5_tunnel_drop")).items() if not k.startswith("__")})

class TestTheKillProducesAResultRatherThanASilence:
    def test_the_match_was_alive_first(self) -> None:
        tunnel = Tunnel()
        orch = peer(tunnel)
        assert orch.call_opponent("receive_turn", TURN)["ok"] is True
        assert orch.client.log.of_kind(CONNECT)
    def test_the_kill_aborts_with_a_named_cause(self) -> None:
        tunnel = Tunnel()
        orch = peer(tunnel)
        orch.call_opponent("receive_turn", TURN)
        tunnel.kill()
        with pytest.raises(MatchAborted) as excinfo:
            orch.call_opponent("receive_turn", {**TURN, "step": 5})
        assert excinfo.value.cause is TechnicalLoss.TIMEOUT
        assert "after 4 attempts" in excinfo.value.detail
        assert LIVE_URL in excinfo.value.detail
    def test_the_cause_survives_propagation(self) -> None:
        tunnel = Tunnel()
        orch = peer(tunnel)
        tunnel.kill()
        try:
            orch.call_opponent("receive_turn", TURN)
        except MatchAborted as aborted:
            assert (aborted.cause, bool(aborted.detail)) == (TechnicalLoss.TIMEOUT, True)
        else:  # pragma: no cover - the call above always raises
            pytest.fail("a dead tunnel must abort")
    def test_it_gives_up_rather_than_retrying_forever(self) -> None:
        tunnel = Tunnel()
        orch = peer(tunnel)
        tunnel.kill()
        with pytest.raises(MatchAborted):
            orch.call_opponent("receive_turn", TURN)
        assert tunnel.calls == 4
    def test_the_state_machine_reaches_a_terminal_phase(self) -> None:
        machine = GamePhaseMachine(Phase.COMPUTING_MOVE)
        tunnel = Tunnel()
        orch = peer(tunnel)
        tunnel.kill()
        try:
            orch.call_opponent("receive_turn", TURN)
        except MatchAborted as aborted:
            machine.abort(str(aborted.cause))
        assert machine.phase is Phase.TECHNICAL_LOSS
        assert machine.is_terminal
    def test_the_scoreboard_is_zero_for_both_sides(self) -> None:
        assert technical_loss_scores() == (0, 0)
