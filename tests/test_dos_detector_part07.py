from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_dos_detector")).items() if not k.startswith("__")})

class TestTheHistoryIsBounded:
    def test_it_does_not_grow_without_limit(self, tmp_path: Path) -> None:
        clock = Clock()
        gate = detector(tmp_path, clock)
        for index in range(200):
            clock.advance(600.0 + (index % 7) * 97.0)
            gate.record()
        assert len(gate.recent) <= gate.history
