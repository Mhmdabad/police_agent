from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_main")).items() if not k.startswith("__")})

class TestSayingWhatWentWrong:
    def test_a_plain_message_is_passed_through(self) -> None:
        assert describe_failure(ValueError("the board is the wrong size")) == (
            "the board is the wrong size (ValueError)"
        )
    def test_an_exception_group_is_unwrapped(self) -> None:
        group = ExceptionGroup("", [ConnectionError("tunnel is down"), TimeoutError("no reply")])
        said = describe_failure(group)
        assert "tunnel is down" in said
        assert "no reply" in said
    def test_several_arguments_are_joined_rather_than_shown_as_a_tuple(self) -> None:
        said = describe_failure(RuntimeError("timeout", "the opponent stopped answering"))
        assert said.startswith("timeout; the opponent stopped answering")
        assert "(" not in said.split("(RuntimeError")[0]
    def test_a_silent_exception_names_its_cause(self) -> None:
        try:
            try:
                raise ConnectionError("nothing is listening behind the tunnel")
            except ConnectionError as inner:
                raise RuntimeError from inner
        except RuntimeError as exc:
            said = describe_failure(exc)
        assert "carried no message" in said
        assert "nothing is listening behind the tunnel" in said
    def test_a_silent_exception_with_no_cause_still_says_something(self) -> None:
        said = describe_failure(RuntimeError())
        assert "RuntimeError" in said
        assert "nothing recorded why" in said
    def test_the_class_is_not_repeated_when_the_message_already_names_it(self) -> None:
        class StartupTimeout(RuntimeError):
            pass
        assert describe_failure(StartupTimeout("StartupTimeout while waiting")) == (
            "StartupTimeout while waiting"
        )
