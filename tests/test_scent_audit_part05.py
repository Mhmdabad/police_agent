from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_scent_audit")).items() if not k.startswith("__")})

class TestTheModelIsTheOneTheBookLocks:
    def test_no_cell_can_exceed_the_appendix_f_centre(self) -> None:
        assert max(check_field(snapshot_at((4, 4)), BOARD).values()) == CENTRE_INTENSITY
    def test_every_reconstructed_value_is_finite_and_in_range(self) -> None:
        for field in trail_snapshots([(4, 4), (4, 5), (4, 6)], BOARD):
            for value in field.values():
                assert math.isfinite(value)
                assert 0.0 < value <= CENTRE_INTENSITY
