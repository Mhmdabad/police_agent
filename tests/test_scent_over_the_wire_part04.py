from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_scent_over_the_wire")).items() if not k.startswith("__")})

class TestDecayRanOncePerFullTurn:
    def test_the_transmitted_trail_matches_the_model_exactly(
        self, played: tuple[Side, Side]
    ) -> None:
        cop, thief = played
        assert cop.sent == trail_snapshots(cells_walked(COP_START, SCRIPT["police"]), GRID)
        assert thief.sent == trail_snapshots(cells_walked(THIEF_START, SCRIPT["thief"]), GRID)
    def test_a_cell_left_behind_fades_rather_than_vanishing(
        self, played: tuple[Side, Side]
    ) -> None:
        _, thief = played
        left_behind = f"{THIEF_START[0]},{THIEF_START[1]}"
        strengths = [field[left_behind] for field in thief.sent if field]
        assert strengths == sorted(strengths, reverse=True)
        assert strengths[-1] > 0.0
