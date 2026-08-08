from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_report")).items() if not k.startswith("__")})

class TestTheAttachmentIsTheReport:
    def test_the_json_is_attached_as_a_file(self) -> None:
        mail = Message(report=report(), sender="cop@example.com").build()
        attachments = list(mail.iter_attachments())
        assert len(attachments) == 1
        assert attachments[0].get_filename() == "result_uoh26-s82kma9e.json"
    def test_the_attachment_is_application_json(self) -> None:
        mail = Message(report=report(), sender="cop@example.com").build()
        assert next(mail.iter_attachments()).get_content_type() == "application/json"
    def test_the_attachment_round_trips_to_the_same_structure(self) -> None:
        mail = Message(report=report(), sender="cop@example.com").build()
        payload = next(mail.iter_attachments()).get_payload(decode=True)
        assert isinstance(payload, bytes)
        assert json.loads(payload) == report().to_dict()
    def test_the_body_carries_nothing_a_parser_would_want(self) -> None:
        body = Message(report=report(), sender="cop@example.com").body()
        assert "100" not in body
        assert "41233" not in body
        assert "not machine-readable on purpose" in body
    def test_the_destination_is_the_hard_coded_lecturer_address(self) -> None:
        mail = Message(report=report(), sender="cop@example.com").build()
        assert mail["To"] == LECTURER == "rmisegal+uoh26finalgame@gmail.com"
    def test_the_subject_names_the_game_and_the_role(self) -> None:
        subject = Message(report=report(), sender="cop@example.com").subject()
        assert "uoh26-s82kma9e" in subject
        assert "police" in subject
