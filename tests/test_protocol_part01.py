from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_protocol")).items() if not k.startswith("__")})

class TestWireVocabulary:
    def test_roles_use_the_reference_names(self) -> None:
        assert {"police", "thief"} == ROLES
    def test_control_kinds_match_the_reference(self) -> None:
        assert {"enable", "status", "restart", "quit"} == CONTROL_KINDS
    def test_tool_names_match_the_reference(self) -> None:
        assert TOOL_NAMES == ("negotiate", "receive_turn", "submit_audit", "receive_control")
