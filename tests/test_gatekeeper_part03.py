from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_gatekeeper")).items() if not k.startswith("__")})

class TestTheBucketSaysNotYetRatherThanNo:
    def test_an_empty_bucket_returns_a_wait(self, tmp_path: Path) -> None:
        gate = gatekeeper(tmp_path)
        gate.admit()
        gate.admit()
        waited = gate.admit()
        assert isinstance(waited, Wait)
        assert waited.seconds == pytest.approx(2.0)
    def test_a_wait_is_not_a_refusal(self, tmp_path: Path) -> None:
        gate = gatekeeper(tmp_path)
        gate.admit()
        gate.admit()
        assert gate.admit() is not None, "a Wait, not an exception"
    def test_a_wait_reads_as_a_sentence(self, tmp_path: Path) -> None:
        assert str(Wait(2.0, "rate limiter: no token available yet")).startswith("wait 2s")
    def test_a_full_queue_is_a_refusal(self, tmp_path: Path) -> None:
        gate = gatekeeper(tmp_path, limit=1000)
        for _ in range(110):
            try:
                gate.admit()
            except Rejected as exc:
                assert "rate limiter" in str(exc)
                return
        pytest.fail("the queue never filled")
    def test_a_wait_does_not_spend_a_quota_slot(self, tmp_path: Path) -> None:
        gate = gatekeeper(tmp_path, limit=50)
        gate.admit()
        gate.admit()
        for _ in range(200):
            assert isinstance(gate.admit(), Wait)
            gate.release()
        assert gate.quota.used() == 2, "only the two that actually went out"
    def test_the_reservation_still_happens_before_the_send(self, tmp_path: Path) -> None:
        gate = gatekeeper(tmp_path)
        assert gate.admit() is None
        assert gate.quota.used() == 1, "reserved by the time admit() returns"
    def test_a_reservation_that_fails_after_the_check_is_still_a_refusal(
        self, tmp_path: Path
    ) -> None:
        gate = gatekeeper(tmp_path)
        class Vanishing(Quota):
            def check(self) -> None:
                return
            def reserve(self, count: int = 1) -> int:
                raise QuotaError("the ledger changed under us")
        gate.quota = Vanishing(path=tmp_path / ".quota_cop.json", limit=10)
        with pytest.raises(Rejected, match="quota: the ledger changed"):
            gate.admit()
    def test_release_frees_a_queue_slot(self, tmp_path: Path) -> None:
        gate = gatekeeper(tmp_path)
        gate.admit()
        gate.admit()
        gate.admit()
        assert gate.limiter.waiting == 1
        gate.release()
        assert gate.limiter.waiting == 0
