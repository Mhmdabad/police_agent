from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_actions")).items() if not k.startswith("__")})

class TestBarrierIsIrreversible:
    def test_barriers_only_ever_grow(self) -> None:
        state = make(cop=(3, 3))
        for cell in ((3, 3), (2, 3), (3, 4)):
            after = place_barrier(state, cell, AXES)
            assert after.barriers >= state.barriers
            state = after
        assert state.barriers == frozenset({(3, 3), (2, 3), (3, 4)})
    def test_no_api_removes_a_barrier(self) -> None:
        import cop_agent.domain.actions as actions
        assert not [n for n in dir(actions) if "remove" in n or "clear" in n]
    def test_replacing_an_existing_barrier_is_refused(self) -> None:
        state = make(cop=(3, 3), barriers=frozenset({(2, 3)}))
        with pytest.raises(IllegalActionError, match="already placed"):
            place_barrier(state, (2, 3), AXES)
