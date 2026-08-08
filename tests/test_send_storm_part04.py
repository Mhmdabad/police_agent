from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_send_storm")).items() if not k.startswith("__")})

class TestTheStormIsRealistic:
    def test_the_payload_is_a_real_report(self, tmp_path: Path) -> None:
        api = CountingApi()
        run_storm(gatekeeper(tmp_path, Clock()), api)
        assert api.calls, "nothing was sent at all, so the test proves nothing"
        assert api.calls[0]["raw"], "the storm sent an empty payload"
    def test_the_loop_has_no_error_handling_of_its_own(self, tmp_path: Path) -> None:
        api = CountingApi()
        storm = run_storm(gatekeeper(tmp_path, Clock()), api)
        assert storm.stopped_by in {"Rejected", "DosDetected"}
