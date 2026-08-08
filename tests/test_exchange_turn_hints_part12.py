from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_exchange_turn_hints")).items() if not k.startswith("__")})

class TestTheSenderSpendsABudgetRatherThanGivingUpOrWaitingForever:
    def a_client(self, inboxes: PeerInboxes) -> OpponentClient:
        def crossing(_: float) -> None:
            inboxes.bind("series-123", 1)
        return OpponentClient(
            transport=Door(inboxes),
            settings=ClientSettings(opponent_url="http://127.0.0.1:1/mcp", retry_backoff_sec=0.0),
            sleep=crossing,
        )
    def test_an_honest_packet_sent_just_before_the_bind_lands_on_the_retry(self) -> None:
        inboxes = PeerInboxes()
        client = self.a_client(inboxes)
        assert client.call("receive_turn", {"message": turn(sub_game=1)}) == {"ok": True}
        assert client.attempts == 2
        assert inboxes.turns.get_nowait().sub_game == 1
        assert inboxes.rejected == []
    def test_a_door_that_never_opens_costs_the_budget_and_then_the_match(self) -> None:
        inboxes = PeerInboxes()
        client = OpponentClient(
            transport=Door(inboxes),
            settings=ClientSettings(
                opponent_url="http://127.0.0.1:1/mcp", max_retries=2, retry_backoff_sec=0.0
            ),
        )
        with pytest.raises(PeerNotReadyError, match="receive_turn"):
            client.call("receive_turn", {"message": turn(sub_game=1)})
        assert client.attempts == 3
        assert inboxes.turns.empty() and inboxes.accepted_turns == {}
    def test_that_exhaustion_is_the_same_technical_loss_an_unreachable_peer_is(self) -> None:
        assert issubclass(PeerNotReadyError, OpponentUnreachableError)
    def test_a_final_refusal_is_not_retried(self) -> None:
        inboxes = PeerInboxes(game_uid="series-123", sub_game=1)
        client = self.a_client(inboxes)
        answer = client.call("receive_turn", {"message": turn(game_uid="other", sub_game=1)})
        assert answer["ok"] is False and client.attempts == 1
    def test_a_re_send_is_the_same_bytes_rather_than_a_second_action(self) -> None:
        inboxes = PeerInboxes()
        client = self.a_client(inboxes)
        client.call("receive_turn", {"message": turn(sub_game=1)})
        assert len({digest for _, digest in client.sent}) == 1
