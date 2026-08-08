from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_quota")).items() if not k.startswith("__")})

class TestCountingAndTheCeiling:
    def test_a_fresh_ledger_starts_at_zero(self, tmp_path: Path) -> None:
        assert quota(tmp_path).used() == 0
        assert quota(tmp_path).remaining() == 3
    def test_reserving_increments(self, tmp_path: Path) -> None:
        gate = quota(tmp_path)
        assert gate.reserve() == 1
        assert gate.reserve() == 2
        assert gate.remaining() == 1
    def test_reserving_past_the_ceiling_is_refused(self, tmp_path: Path) -> None:
        gate = quota(tmp_path)
        for _ in range(3):
            gate.reserve()
        with pytest.raises(QuotaExhausted, match="3 of 3 sends used"):
            gate.reserve()
    def test_a_refused_reservation_does_not_burn_the_slot(self, tmp_path: Path) -> None:
        gate = quota(tmp_path)
        gate.reserve(2)
        with pytest.raises(QuotaExhausted):
            gate.reserve(2)
        assert gate.used() == 2
        assert gate.reserve() == 3
    def test_a_multi_slot_reservation_is_all_or_nothing(self, tmp_path: Path) -> None:
        gate = quota(tmp_path)
        with pytest.raises(QuotaExhausted):
            gate.reserve(4)
        assert gate.used() == 0
    def test_check_reports_without_spending(self, tmp_path: Path) -> None:
        gate = quota(tmp_path)
        gate.check()
        assert gate.used() == 0
    def test_check_raises_once_the_ceiling_is_reached(self, tmp_path: Path) -> None:
        gate = quota(tmp_path)
        gate.reserve(3)
        with pytest.raises(QuotaExhausted, match="does not yield to a retry"):
            gate.check()
    def test_a_reservation_of_zero_is_a_mistake_not_a_no_op(self, tmp_path: Path) -> None:
        with pytest.raises(QuotaError, match="at least one send"):
            quota(tmp_path).reserve(0)
