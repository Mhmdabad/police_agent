from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_mailer")).items() if not k.startswith("__")})

class TestAReportGetsSent:
    def test_exactly_one_message_reaches_the_api(self, tmp_path: Path) -> None:
        mailer, api, _ = a_mailer(tmp_path)
        mailer.send_report(a_report(), "cop@example.com")
        assert len(api.calls) == 1
    def test_the_api_answer_comes_back(self, tmp_path: Path) -> None:
        mailer, _, _ = a_mailer(tmp_path)
        assert mailer.send_report(a_report(), "cop@example.com")["labelIds"] == ["SENT"]
    def test_what_is_sent_is_the_json_attachment(self, tmp_path: Path) -> None:
        import base64
        from email import message_from_bytes
        from email.policy import default
        mailer, api, _ = a_mailer(tmp_path)
        mailer.send_report(a_report(), "cop@example.com")
        mime = message_from_bytes(base64.urlsafe_b64decode(api.calls[0]["raw"]), policy=default)
        attached = next(mime.iter_attachments()).get_payload(decode=True)
        assert isinstance(attached, bytes)
        assert json.loads(attached)["game_uid"] == "u-0001"
    def test_it_goes_to_the_hard_coded_lecturer(self, tmp_path: Path) -> None:
        import base64
        from email import message_from_bytes
        from email.policy import default
        mailer, api, _ = a_mailer(tmp_path)
        mailer.send_report(a_report(), "cop@example.com")
        mime = message_from_bytes(base64.urlsafe_b64decode(api.calls[0]["raw"]), policy=default)
        assert mime["To"] == LECTURER
