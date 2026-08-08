from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_quota")).items() if not k.startswith("__")})

class TestReservingBeforeTheSendNotAfter:
    def test_a_send_that_fails_after_reserving_still_counts(self, tmp_path: Path) -> None:
        gate = quota(tmp_path)
        gate.reserve()
        with pytest.raises(RuntimeError):
            raise RuntimeError("the API call blew up after the message went out")
        assert gate.used() == 1
    def test_counting_after_success_would_never_reach_the_ceiling(self, tmp_path: Path) -> None:
        gate = quota(tmp_path)
        for _ in range(10):
            gate.check()  # a caller that only records on success
        assert gate.used() == 0, "checking without reserving spends nothing — hence reserve()"
