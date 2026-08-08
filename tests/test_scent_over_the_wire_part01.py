from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_scent_over_the_wire")).items() if not k.startswith("__")})

class TestTheFieldActuallyCrossesTheWire:
    def test_each_side_receives_exactly_one_identical_hint_per_step(
        self, played: tuple[Side, Side]
    ) -> None:
        cop, thief = played
        assert cop.game.received_hints == {step: "over there" for step in range(1, STEPS + 1)}
        assert thief.game.received_hints == {step: "over there" for step in range(1, STEPS + 1)}
    def test_both_sides_transmitted_a_non_empty_field_every_step(
        self, played: tuple[Side, Side]
    ) -> None:
        for side in played:
            assert all(field for field in side.sent), f"{side.role} sent nothing"
    def test_each_side_received_what_the_other_sent(self, played: tuple[Side, Side]) -> None:
        cop, thief = played
        assert cop.received == thief.sent
        assert thief.received == cop.sent
    def test_the_field_survives_the_wire_unrounded(self, played: tuple[Side, Side]) -> None:
        cop, _ = played
        for field in cop.received:
            assert field == json.loads(json.dumps(field))
