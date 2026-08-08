from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_localhost_match")).items() if not k.startswith("__")})

class TestTheSeriesOpenedOnALockedScentModel:
    def test_both_sides_locked_the_same_model(self, played: tuple[Side, Side, Path]) -> None:
        cop, thief, _ = played
        assert cop.runner.scent_lock == thief.runner.scent_lock == propose().agreement()
    def test_both_gates_ran_in_order_and_before_the_board(
        self, played: tuple[Side, Side, Path]
    ) -> None:
        cop, _, _ = played
        beats = cop.runner.orchestrator.heartbeats
        assert [beat for beat in beats if not beat.startswith(("attempt:", "outbound:"))] == [
            "negotiate_config",
            "await_config",
            "negotiate_scent",
            "await_scent",
        ]
        assert cop.runner.outcomes[0].log.entries
    def test_the_sub_game_took_its_scent_rule_from_the_agreement(
        self, played: tuple[Side, Side, Path]
    ) -> None:
        for side in played[:2]:
            assert side.runner.scent_lock is not None
            assert (
                played_game(side).require_bound_scent
                is side.runner.scent_lock.require_bound_scent
                is True
            )
