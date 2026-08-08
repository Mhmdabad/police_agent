from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_mcp_client")).items() if not k.startswith("__")})

class TestARetryReSendsBytesNotAnIntention:
    def test_every_attempt_carries_the_original_payload(self) -> None:
        transport = MutatingTransport(failures=2)
        OpponentClient(transport, SETTINGS).call("receive_turn", {"move": "N", "step": 4})
        assert transport.seen == [{"move": "N", "step": 4}] * 3
    def test_a_caller_mutating_between_attempts_cannot_change_the_action(self) -> None:
        payload = {"move": "N", "commit": "a" * 64}
        transport = FakeTransport(TimeoutError(), {"ok": True})
        client = OpponentClient(transport, SETTINGS)
        original = dict(payload)
        payload["move"] = "S"  # the caller changes its mind mid-flight
        client.call("receive_turn", original)
        assert [c["payload"] for c in transport.calls] == [original] * 2
    def test_the_transport_is_handed_a_fresh_object_each_attempt(self) -> None:
        transport = MutatingTransport(failures=1)
        OpponentClient(transport, SETTINGS).call("receive_turn", {"move": "E"})
        assert transport.seen[0] == transport.seen[1] == {"move": "E"}
    def test_it_records_a_digest_of_what_was_sent(self) -> None:
        client = OpponentClient(FakeTransport(TimeoutError(), {"ok": True}), SETTINGS)
        client.call("receive_turn", {"move": "N"})
        client.call("receive_turn", {"move": "N"})
        tools = [tool for tool, _ in client.sent]
        digests = [digest for _, digest in client.sent]
        assert tools == ["receive_turn", "receive_turn"]
        assert digests[0] == digests[1]
        assert len(client.sent) == 2  # two calls, four attempts
    def test_key_order_does_not_change_the_digest(self) -> None:
        client = OpponentClient(FakeTransport(), SETTINGS)
        client.call("receive_turn", {"move": "N", "step": 1})
        client.call("receive_turn", {"step": 1, "move": "N"})
        assert client.sent[0][1] == client.sent[1][1]
    def test_an_unserialisable_payload_fails_before_the_first_attempt(self) -> None:
        transport = FakeTransport()
        with pytest.raises(TypeError):
            OpponentClient(transport, SETTINGS).call("receive_turn", {"move": {1, 2}})
        assert transport.calls == []
