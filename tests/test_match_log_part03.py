from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_match_log")).items() if not k.startswith("__")})

class TestNoncesArriveLast:
    def test_a_running_match_has_unopened_steps(self) -> None:
        written = log()
        written.commit(1, DIGEST)
        written.reveal(1, OPENED)
        assert written.unopened() == [1]
    def test_an_empty_list_is_the_only_acceptable_end_state(self) -> None:
        assert played(3).unopened() == []
    def test_a_partially_opened_match_names_the_gaps(self) -> None:
        written = played(2)
        written.commit(3, DIGEST)
        written.reveal(3, OPENED)
        assert written.unopened() == [3]
