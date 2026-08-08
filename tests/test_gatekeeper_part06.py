from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_gatekeeper")).items() if not k.startswith("__")})

class TestReadingTheStatusCode:
    def test_the_constant_is_429(self) -> None:
        assert TOO_MANY_REQUESTS == 429
    def test_a_bare_integer(self) -> None:
        assert status_code_of(429) == 429
    def test_a_status_code_attribute(self) -> None:
        class Error:
            status_code = 429
        assert status_code_of(Error()) == 429
    def test_a_google_http_error_shape(self) -> None:
        class Response:
            status = 429
        class HttpError:
            resp = Response()
        assert status_code_of(HttpError()) == 429
    def test_a_code_attribute(self) -> None:
        class Error:
            code = 503
        assert status_code_of(Error()) == 503
    def test_something_with_no_status_at_all(self) -> None:
        assert status_code_of(ValueError("network went away")) is None
    def test_a_non_integer_status_is_not_taken(self) -> None:
        class Error:
            status_code = "429"
        assert status_code_of(Error()) is None
    def test_a_caller_may_supply_its_own_reader(self) -> None:
        assert status_code_of("whatever", reader=lambda _: 429) == 429
    def test_reading_several_shapes_is_the_point(self) -> None:
        class ByAttribute:
            status_code = 429
        class ByResponse:
            class resp:  # noqa: N801
                status = 429
        assert {
            status_code_of(429),
            status_code_of(ByAttribute()),
            status_code_of(ByResponse()),
        } == {429}
