from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_main")).items() if not k.startswith("__")})

class TestTheReporterCannotBecomeTheFailure:
    def cyclic(self) -> BaseException:
        leaf = RuntimeError()
        group = ExceptionGroup("", [leaf])
        leaf.__context__ = group
        return group
    def test_a_cycle_terminates(self) -> None:
        assert "RuntimeError" in describe_failure(self.cyclic())
    def test_a_cycle_terminates_through_the_safe_wrapper_too(self) -> None:
        assert safely_describe(self.cyclic())
    def test_a_long_chain_stops_before_it_becomes_noise(self) -> None:
        deepest = ValueError("the bottom")
        current: BaseException = deepest
        for _ in range(MAX_DEPTH * 3):
            nxt = RuntimeError()
            nxt.__cause__ = current
            current = nxt
        said = describe_failure(current)
        assert "the bottom" not in said, "walked further than the depth bound"
    def test_the_same_leaf_twice_is_said_once(self) -> None:
        one = ConnectionError("nothing is listening behind the tunnel")
        said = describe_failure(ExceptionGroup("", [one, ConnectionError(str(one))]))
        assert said.count("nothing is listening") == 1
    def test_a_reporter_that_explodes_still_reports(self) -> None:
        class Hostile(Exception):
            def __str__(self) -> str:
                raise RecursionError("boom")
        said = safely_describe(Hostile())
        assert "the failure description itself failed" in said
        assert "Hostile" in said
