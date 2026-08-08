from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_artefacts")).items() if not k.startswith("__")})

class TestACoherentSet:
    def test_it_agrees_on_one_match(self) -> None:
        assert a_set().check().coherent
        assert "agree on one match" in str(a_set().check())
    def test_the_declaration_is_authoritative_for_the_uid(self) -> None:
        assert a_set().game_uid == UID
    def test_every_name_derives_from_the_game_id(self) -> None:
        assert a_set().filenames() == (
            "declaration_uoh26-s82kma9e.json",
            "config_uoh26-s82kma9e_g01.json",
            "config_uoh26-s82kma9e_g02.json",
            "log_uoh26-s82kma9e_g01.json",
            "log_uoh26-s82kma9e_g02.json",
            "result_uoh26-s82kma9e.json",
        )
    def test_the_names_are_all_distinct(self) -> None:
        names = a_set().filenames()
        assert len(set(names)) == len(names)
