from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_report")).items() if not k.startswith("__")})

class TestTheGmailPayload:
    def test_it_is_url_safe_base64(self) -> None:
        raw = Message(report=report(), sender="cop@example.com").raw()["raw"]
        assert "+" not in raw and "/" not in raw
    def test_it_decodes_back_to_the_mime_message(self) -> None:
        message = Message(report=report(), sender="cop@example.com")
        decoded = message_from_bytes(
            base64.urlsafe_b64decode(message.raw()["raw"]), policy=default_policy
        )
        assert decoded["To"] == LECTURER
    def test_the_attachment_survives_the_encoding(self) -> None:
        message = Message(report=report(), sender="cop@example.com")
        decoded = message_from_bytes(
            base64.urlsafe_b64decode(message.raw()["raw"]), policy=default_policy
        )
        attached = next(decoded.iter_attachments()).get_payload(decode=True)
        assert isinstance(attached, bytes)
        assert json.loads(attached)["totals"]["total_tokens"] == 41_233
    def test_building_twice_does_not_attach_twice(self) -> None:
        message = Message(report=report(), sender="cop@example.com")
        message.build()
        decoded = message_from_bytes(
            base64.urlsafe_b64decode(message.raw()["raw"]), policy=default_policy
        )
        assert len(list(decoded.iter_attachments())) == 1
    def test_raw_builds_on_demand(self) -> None:
        assert "raw" in Message(report=report(), sender="cop@example.com").raw()
