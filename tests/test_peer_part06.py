from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_peer")).items() if not k.startswith("__")})

class TestReceivingACommitment:
    def test_a_turn_becomes_a_commitment(self) -> None:
        from cop_agent.infra.protocol import TurnMessage
        peer, _, inboxes = a_peer()
        inboxes.turns.put(
            TurnMessage(
                step=1,
                sender="thief",
                hint="",
                smell_grid={},
                commit=OTHER,
                timestamp=WHEN,
            )
        )
        received = peer.await_commit(1)
        assert received.commit == OTHER
        assert received.sender == "thief"
    def test_the_opponent_of_the_thief_is_the_police(self) -> None:
        peer, _, _ = a_peer()
        peer.role = "thief"
        assert peer.opponent == "police"
    def test_it_waits_again_when_a_payload_holds_nothing_wanted(self) -> None:
        peer, _, inboxes = a_peer(timeout=2.0)
        other = Reveal(step=9, sender="thief", move="E", intent="truth", hint="t", timestamp=WHEN)
        wanted = Reveal(step=1, sender="thief", move="S", intent="truth", hint="t", timestamp=WHEN)
        spare = Reveal(step=8, sender="thief", move="W", intent="truth", hint="t", timestamp=WHEN)
        inboxes.audits.put(
            AuditPayload(
                sender="thief",
                records=[other.to_dict(), spare.to_dict()],
                result_claim=UNDECIDED,
                game_uid="series-123",
                sub_game=2,
            )
        )
        inboxes.audits.put(
            AuditPayload(
                sender="thief",
                records=[wanted.to_dict()],
                result_claim=UNDECIDED,
                game_uid="series-123",
                sub_game=2,
            )
        )
        assert peer.await_reveal(1).move == "S"
        assert peer.await_reveal(8).move == "W", "held records are searched, not just the first"
        assert peer.await_reveal(9).move == "E", "the first payload was not kept"
