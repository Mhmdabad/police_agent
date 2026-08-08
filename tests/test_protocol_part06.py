from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_protocol")).items() if not k.startswith("__")})

class TestRegistration:
    def test_all_four_tools_are_exposed(self) -> None:
        host = RecordingHost()
        assert register(host, PeerInboxes()) == TOOL_NAMES
        assert host.registered == list(TOOL_NAMES)
    def test_no_extra_tools_are_exposed(self) -> None:
        host = RecordingHost()
        register(host, PeerInboxes())
        assert len(host.registered) == 4
