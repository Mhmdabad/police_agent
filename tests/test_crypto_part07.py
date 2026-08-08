from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_crypto")).items() if not k.startswith("__")})

class TestWhatABoardStateSeals:
    def test_it_seals_our_own_cell(self) -> None:
        assert board_terms(BOARD, "police")["self"] == [1, 2]
        assert board_terms(BOARD, "thief")["self"] == [6, 5]
    def test_it_never_seals_our_belief_about_the_opponent(self) -> None:
        terms = board_terms(BOARD, "police")
        assert "thief" not in terms
        assert [6, 5] not in terms.values()
    def test_every_sealed_field_is_checkable_by_the_opponent(self) -> None:
        assert set(board_terms(BOARD, "police")) == {"grid_size", "step", "self", "barriers"}
    def test_barriers_are_sorted_so_set_order_cannot_reach_the_digest(self) -> None:
        shuffled = BoardState(
            grid_size=8, cop=(1, 2), thief=(6, 5), barriers=frozenset({(0, 1), (3, 3)}), step=4
        )
        assert board_terms(BOARD, "police") == board_terms(shuffled, "police")
        assert board_terms(BOARD, "police")["barriers"] == [[0, 1], [3, 3]]
    def test_positions_are_lists_because_that_is_what_survives_json(self) -> None:
        terms = board_terms(BOARD, "police")
        assert json.loads(canonical(terms)) == terms
    def test_the_step_binds_the_commitment_to_one_turn(self) -> None:
        later = BoardState(grid_size=8, cop=(1, 2), thief=(6, 5), barriers=BOARD.barriers, step=5)
        assert board_terms(BOARD, "police") != board_terms(later, "police")
    def test_a_role_the_wire_does_not_name_is_refused(self) -> None:
        with pytest.raises(CryptoError, match="role must be one of"):
            board_terms(BOARD, "cop")
