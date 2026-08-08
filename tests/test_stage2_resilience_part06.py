from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_stage2_resilience")).items() if not k.startswith("__")})

class TestBarrierDeclarationCannotBeBypassed:
    def test_the_turn_message_is_the_only_declaration_channel(self) -> None:
        import cop_agent.infra.inboxes as inboxes
        import cop_agent.infra.protocol as protocol
        assert "barrier_placed" in protocol.TurnMessage.__dataclass_fields__
        assert inboxes.TOOL_NAMES == (
            "negotiate",
            "receive_turn",
            "submit_audit",
            "receive_control",
        )
    def test_no_separate_barrier_tool_survives(self) -> None:
        import cop_agent.infra.inboxes as inboxes
        assert not [n for n in dir(inboxes.PeerInboxes) if "barrier" in n]
    def test_a_declared_placement_arrives_with_its_turn(self) -> None:
        from cop_agent.infra.protocol import TurnMessage
        parsed = TurnMessage.from_dict(
            {
                "step": 9,
                "sender": "police",
                "smell_grid": {},
                "commit": "c",
                "timestamp": "t",
                "game_uid": "series-123",
                "sub_game": 1,
                "barrier_placed": [2, 3],
            }
        )
        assert parsed.barrier_placed == [2, 3]
        assert parsed.step == 9
