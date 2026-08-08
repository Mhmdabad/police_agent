from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_orchestrator")).items() if not k.startswith("__")})

class TestHandshakeChecks:
    def test_our_greeting_takes_its_role_from_the_orchestrator(self) -> None:
        orch, _ = orchestrator()
        assert orch.greeting(OUR_URL, "s82kma9e").role == "police"
    def test_announcing_pushes_the_address_through_negotiate(self) -> None:
        orch, transport = orchestrator()
        orch.announce(orch.greeting(OUR_URL, "s82kma9e"))
        assert transport.calls[0]["tool"] == "negotiate"
        assert (
            transport.calls[0]["payload"]["message"]["greeting"]["public_url"] == f"{OUR_URL}/mcp"
        )
    def test_a_matching_protocol_and_opposite_role_passes(self) -> None:
        orch, _ = orchestrator()
        inbound(orch)
        assert orch.accept_greeting(orch.greeting(OUR_URL, "s82kma9e")).role == "thief"
    def test_a_protocol_mismatch_aborts(self) -> None:
        orch, _ = orchestrator()
        inbound(orch, version="0.9")
        with pytest.raises(MatchAborted, match="wire contract must match"):
            orch.accept_greeting(orch.greeting(OUR_URL, "s82kma9e"))
    def test_a_duplicate_role_aborts(self) -> None:
        orch, _ = orchestrator()
        inbound(orch, role="police")
        with pytest.raises(MatchAborted, match="no capture target"):
            orch.accept_greeting(orch.greeting(OUR_URL, "s82kma9e"))
    @pytest.mark.parametrize("role", ["referee", "cop"])
    def test_a_role_the_wire_does_not_name_aborts(self, role: str) -> None:
        orch, _ = orchestrator()
        inbound(orch, role=role)
        with pytest.raises(MatchAborted, match="role must be one of"):
            orch.accept_greeting(orch.greeting(OUR_URL, "s82kma9e"))
    def test_an_unreachable_opponent_aborts_when_we_are_public(self) -> None:
        orch, _ = orchestrator()
        inbound(orch, url="http://127.0.0.1:8802")
        with pytest.raises(MatchAborted, match="routes nowhere"):
            orch.accept_greeting(orch.greeting(OUR_URL, "s82kma9e"))
    def test_the_newest_greeting_wins_over_a_stale_one(self) -> None:
        orch, _ = orchestrator()
        inbound(orch, url="https://thief-stale.ngrok-free.app")
        inbound(orch, url="https://thief-fresh.ngrok-free.app")
        accepted = orch.accept_greeting(orch.greeting(OUR_URL, "s82kma9e"))
        assert accepted.public_url == "https://thief-fresh.ngrok-free.app/mcp"
    def test_the_stale_greetings_are_drained_not_left_behind(self) -> None:
        orch, _ = orchestrator()
        inbound(orch, url="https://thief-stale.ngrok-free.app")
        inbound(orch, url="https://thief-fresh.ngrok-free.app")
        orch.accept_greeting(orch.greeting(OUR_URL, "s82kma9e"))
        assert orch.inboxes.agreements.empty()
    def test_a_single_greeting_still_works(self) -> None:
        orch, _ = orchestrator()
        inbound(orch)
        assert orch.accept_greeting(orch.greeting(OUR_URL, "s82kma9e")).public_url == (
            f"{THEIR_URL}/mcp"
        )
    def test_silence_is_a_timeout_not_a_longer_wait(self) -> None:
        orch, _ = orchestrator()
        with pytest.raises(MatchAborted, match="no greeting from the opponent") as excinfo:
            orch.accept_greeting(orch.greeting(OUR_URL, "s82kma9e"), timeout=0.0)
        assert excinfo.value.cause is TechnicalLoss.TIMEOUT
    def test_the_cause_is_recorded(self) -> None:
        orch, _ = orchestrator()
        inbound(orch, role="police")
        with pytest.raises(MatchAborted) as excinfo:
            orch.accept_greeting(orch.greeting(OUR_URL, "s82kma9e"))
        assert excinfo.value.cause is TechnicalLoss.ILLEGAL_ACTION
