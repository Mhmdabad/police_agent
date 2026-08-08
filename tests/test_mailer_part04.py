from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_mailer")).items() if not k.startswith("__")})

class TestOtherFailuresAreNotSwallowed:
    def test_a_non_429_error_propagates(self, tmp_path: Path) -> None:
        class Broken(Exception):
            status_code = 500
        api = CountingApi(fail_with=[Broken()])
        mailer, _, _ = a_mailer(tmp_path)
        mailer.sender = api
        with pytest.raises(Broken):
            mailer.send_report(a_report(), "cop@example.com")
    def test_it_is_not_retried(self, tmp_path: Path) -> None:
        class Broken(Exception):
            status_code = 500
        api = CountingApi(fail_with=[Broken(), Broken()])
        mailer, _, _ = a_mailer(tmp_path)
        mailer.sender = api
        with pytest.raises(Broken):
            mailer.send_report(a_report(), "cop@example.com")
        assert len(api.calls) == 1
