from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_mailer")).items() if not k.startswith("__")})

class TestNothingHereMailsAnybody:
    def test_the_module_names_no_credentials(self) -> None:
        source = (
            Path(__file__).resolve().parent.parent / "src/cop_agent/infra/mailer.py"
        ).read_text()
        assert "credentials.json" not in source
        assert "token_cop.json" not in source
    def test_the_note_says_a_real_send_is_a_human_decision(self) -> None:
        assert "not" in LECTURER_NOTE.lower()
