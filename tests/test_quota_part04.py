from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_quota")).items() if not k.startswith("__")})

class TestTheDayRollsOverInUtc:
    def test_a_new_day_starts_the_count_again(self, tmp_path: Path) -> None:
        clock = Clock()
        gate = quota(tmp_path, clock=clock)
        gate.reserve(3)
        clock.advance(days=1)
        assert gate.used() == 0
        assert gate.reserve() == 1
    def test_later_the_same_day_does_not_roll_over(self, tmp_path: Path) -> None:
        clock = Clock()
        gate = quota(tmp_path, clock=clock)
        gate.reserve(2)
        clock.advance(hours=11)
        assert gate.used() == 2
    def test_the_boundary_is_utc_midnight(self, tmp_path: Path) -> None:
        clock = Clock(datetime(2026, 8, 5, 23, 59, tzinfo=UTC))
        gate = quota(tmp_path, clock=clock)
        gate.reserve(3)
        clock.advance(minutes=2)
        assert gate.used() == 0, "a ceiling that moves with local time is wrong twice a year"
    def test_a_ledger_from_another_day_is_not_carried_forward(self, tmp_path: Path) -> None:
        path = tmp_path / ".quota_cop.json"
        path.write_text(json.dumps({"day": "2020-01-01", "used": 99}))
        assert quota(tmp_path).used() == 0
