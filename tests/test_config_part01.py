from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_config")).items() if not k.startswith("__")})

class TestTable:
    def test_every_status_is_represented(self) -> None:
        assert {p.status for p in TABLE} == set(Status)
    def test_no_duplicate_parameters(self) -> None:
        keys = [(p.section, p.key) for p in TABLE]
        assert len(keys) == len(set(keys))
    def test_scoring_is_entirely_fixed(self) -> None:
        scoring = [p for p in TABLE if p.section == "scoring"]
        assert len(scoring) == 6
        assert all(p.status is Status.FIXED for p in scoring)
    def test_pheromones_are_entirely_fixed(self) -> None:
        pher = [p for p in TABLE if p.section == "pheromones"]
        assert len(pher) == 3
        assert all(p.status is Status.FIXED for p in pher)
    def test_rate_limits_are_minimums(self) -> None:
        limiter = [p for p in TABLE if p.section == "rate_limiter_gatekeeper"]
        assert len(limiter) == 5
        assert all(p.status is Status.MINIMUM for p in limiter)
