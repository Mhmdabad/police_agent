from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_verdict")).items() if not k.startswith("__")})

class TestItAbortsOnFirstFailure:
    def test_the_walk_stops_rather_than_gathering_a_list(self, tmp_path: Path) -> None:
        result = walk(load(sealed_log(tmp_path, steps=6, corrupt=2)))
        assert result.verified == 1
        assert result.total == 6
        assert result.at_step == 2
    def test_it_stops_at_the_earliest_failure_not_the_worst(self, tmp_path: Path) -> None:
        path = sealed_log(tmp_path, steps=6, corrupt=5)
        def edit(body: dict[str, Any]) -> None:
            body["steps"][2]["nonce"] = f"{77:032x}"
        assert walk(load(hand_edited(path, edit))).at_step == 3
    def test_it_walks_the_log_not_the_cursor(self, tmp_path: Path) -> None:
        replay = load(sealed_log(tmp_path, corrupt=2))
        replay.seek(4)
        assert walk(replay).at_step == 2
        assert replay.current.step == 4, "the walk reports; seeking is the viewer's move"
