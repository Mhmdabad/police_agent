from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_quota")).items() if not k.startswith("__")})

class TestTheCountSurvivesTheProcess:
    def test_a_new_instance_sees_what_the_old_one_spent(self, tmp_path: Path) -> None:
        quota(tmp_path).reserve(2)
        assert quota(tmp_path).used() == 2, "an in-memory counter would read zero here"
    def test_a_crash_loop_cannot_reset_the_ceiling(self, tmp_path: Path) -> None:
        sent = 0
        for _ in range(20):
            gate = quota(tmp_path)  # a brand-new process each time
            try:
                gate.reserve()
            except QuotaExhausted:
                continue
            sent += 1
        assert sent == 3, f"the loop got {sent} sends out past a ceiling of 3"
    def test_the_ledger_is_readable_only_by_its_owner(self, tmp_path: Path) -> None:
        gate = quota(tmp_path)
        gate.reserve()
        assert stat.S_IMODE(gate.path.stat().st_mode) == 0o600
