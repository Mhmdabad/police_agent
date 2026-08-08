from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_protocol")).items() if not k.startswith("__")})

class TestNegotiateCarriesTwoKindsOfMessage:
    def greeting(self) -> dict[str, object]:
        return {
            "greeting": {
                "role": "thief",
                "group_id": "them",
                "public_url": "https://x/mcp",
                "protocol_version": "1.0",
            }
        }
    def test_a_greeting_goes_to_agreements(self) -> None:
        inboxes = PeerInboxes()
        assert inboxes.negotiate(self.greeting())["ok"] is True
        assert inboxes.agreements.get_nowait() == self.greeting()
        assert inboxes.digests.empty()
    def test_a_digest_goes_to_digests(self) -> None:
        inboxes = PeerInboxes()
        assert inboxes.negotiate({"config_sha256": "a" * 64})["ok"] is True
        assert inboxes.digests.get_nowait()["config_sha256"] == "a" * 64
        assert inboxes.agreements.empty()
    def test_a_digest_cannot_be_mistaken_for_the_newest_greeting(self) -> None:
        inboxes = PeerInboxes()
        inboxes.negotiate(self.greeting())
        inboxes.negotiate({"config_sha256": "a" * 64})
        assert inboxes.agreements.get_nowait() == self.greeting()
    def test_an_unrecognised_message_is_treated_as_a_greeting(self) -> None:
        inboxes = PeerInboxes()
        inboxes.negotiate({"something": "unexpected"})
        assert inboxes.agreements.get_nowait() == {"something": "unexpected"}
    def test_a_non_mapping_is_still_refused(self) -> None:
        inboxes = PeerInboxes()
        assert inboxes.negotiate("not an object")["ok"] is False
        assert inboxes.agreements.empty()
        assert inboxes.digests.empty()
