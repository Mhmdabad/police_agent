from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_report")).items() if not k.startswith("__")})

class TestTheReportIsAStructure:
    def test_it_serialises_to_json(self) -> None:
        assert json.loads(report().to_json())["game_id"] == "uoh26-s82kma9e"
    def test_it_carries_a_schema_version(self) -> None:
        assert json.loads(report().to_json())["schema_version"] == SCHEMA_VERSION
    def test_the_bytes_are_stable_between_peers(self) -> None:
        assert report().to_json() == report().to_json()
        assert report().to_json().endswith("}\n")
    def test_totals_are_derived_not_restated(self) -> None:
        body = json.loads(report().to_json())
        assert body["totals"]["cop"] == 100
        assert body["totals"]["thief"] == 80
        assert body["totals"]["sub_games_played"] == 2
    def test_the_filename_derives_from_the_game_id(self) -> None:
        assert report().filename == "result_uoh26-s82kma9e.json"
