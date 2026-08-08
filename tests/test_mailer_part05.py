from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_mailer")).items() if not k.startswith("__")})

class TestReadingRetryAfter:
    def test_from_a_google_style_header(self) -> None:
        assert retry_after_of(TooMany(retry_after="42")) == 42.0
    def test_a_lowercase_header(self) -> None:
        error = TooMany()
        error.resp.headers = {"retry-after": "7"}
        assert retry_after_of(error) == 7.0
    def test_a_direct_attribute(self) -> None:
        class Simple:
            retry_after = 12
        assert retry_after_of(Simple()) == 12.0
    def test_nothing_at_all(self) -> None:
        assert retry_after_of(ValueError("network")) is None
    def test_a_header_that_is_not_a_number(self) -> None:
        assert retry_after_of(TooMany(retry_after="Wed, 21 Oct 2026 07:28:00 GMT")) is None
    def test_a_header_of_the_wrong_type(self) -> None:
        error = TooMany()
        error.resp.headers = {"Retry-After": []}
        assert retry_after_of(error) is None
