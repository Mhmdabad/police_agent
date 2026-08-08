from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_scent_audit")).items() if not k.startswith("__")})

class TestAFieldIsValidatedBeforeAnythingReadsIt:
    def test_an_honest_emission_is_accepted(self) -> None:
        parsed = check_field(snapshot_at((4, 4)), BOARD)
        assert parsed[(4, 4)] == CENTRE_INTENSITY
    def test_a_non_object_is_refused(self) -> None:
        with pytest.raises(ScentFieldError):
            check_field([], BOARD)  # type: ignore[arg-type]
    def test_a_non_string_key_is_refused(self) -> None:
        with pytest.raises(ScentFieldError):
            check_field({4: 0.9}, BOARD)  # type: ignore[dict-item]
    @pytest.mark.parametrize("key", ["3", "a,b", "1,2,3", " 1,2", "-1,2", "1, 2", "", "1,"])
    def test_a_malformed_cell_key_is_refused(self, key: str) -> None:
        with pytest.raises(ScentFieldError, match="cell"):
            check_field({key: 0.5}, BOARD)
    def test_a_cell_off_the_board_is_refused(self) -> None:
        with pytest.raises(ScentFieldError, match="off"):
            check_field({f"{BOARD},0": 0.5}, BOARD)
    @pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
    def test_a_non_finite_intensity_is_refused(self, value: float) -> None:
        with pytest.raises(ScentFieldError, match="finite"):
            check_field({"1,1": value}, BOARD)
    def test_a_negative_intensity_is_refused(self) -> None:
        with pytest.raises(ScentFieldError, match="negative"):
            check_field({"1,1": -0.5}, BOARD)
    def test_an_intensity_above_the_centre_is_refused(self) -> None:
        with pytest.raises(ScentFieldError, match="0.9"):
            check_field({"1,1": 1.5}, BOARD)
    def test_a_boolean_is_not_an_intensity(self) -> None:
        with pytest.raises(ScentFieldError, match="number"):
            check_field({"1,1": True}, BOARD)
    def test_a_string_is_not_an_intensity(self) -> None:
        with pytest.raises(ScentFieldError, match="number"):
            check_field({"1,1": "0.9"}, BOARD)  # type: ignore[dict-item]
    def test_more_cells_than_the_board_has_is_refused(self) -> None:
        oversized = {f"{r},{c}": 0.1 for r in range(BOARD) for c in range(BOARD)}
        oversized["0,0"] = 0.1
        check_field(oversized, BOARD)  # exactly board_size**2 is legitimate
        with pytest.raises(ScentFieldError, match="cells"):
            check_field(oversized, 3)
    def test_more_precision_than_the_wire_carries_is_refused(self) -> None:
        with pytest.raises(ScentFieldError, match="precision"):
            check_field({"1,1": 0.123456}, BOARD)
